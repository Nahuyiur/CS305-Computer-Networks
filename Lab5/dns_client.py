#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import random
import socket
import dns.message
import dns.name
import dns.query
import dns.rdatatype as rdatatype
import dns.resolver

# 一组根服务器的IPv4（节选，可全部列出）
ROOT_SERVERS = [
    "198.41.0.4",      # a.root-servers.net
    "199.9.14.201",    # b.root-servers.net
    "192.33.4.12",     # c.root-servers.net
    "199.7.91.13",     # d.root-servers.net
    "192.203.230.10",  # e.root-servers.net
    "192.5.5.241",     # f.root-servers.net
    "192.112.36.4",    # g.root-servers.net
    "198.97.190.53",   # h.root-servers.net
    "192.36.148.17",   # i.root-servers.net
    "192.58.128.30",   # j.root-servers.net
    "193.0.14.129",    # k.root-servers.net
    "199.7.83.42",     # l.root-servers.net
    "202.12.27.33",    # m.root-servers.net
]

SUPPORTED_TYPES = {"A", "AAAA", "CNAME", "NS", "MX"}

def rd1_recursive_query(name: str, qtype: str, server: str | None):
    """
    递归查询（RD=1）：交给递归解析器（本机或指定server）完成。
    """
    # 构建查询报文（dnspython resolver 会自动设置 RD=1）
    r = dns.resolver.Resolver(configure=True)  # 读系统DNS
    r.use_edns(0, ednsflags=0, payload=1232)   # 关闭DNSSEC标志即可，EDNS不是必需
    if server:
        r.nameservers = [server]

    answer = r.resolve(name, qtype, raise_on_no_answer=False)
    # 取底层响应消息
    resp = answer.response
    return resp

def extract_ns_ips(resp):
    """
    从 Authority/Additional 提取下一跳NS的IP（优先用Additional里的Glue）
    返回ip列表；若需要先解析NS的主机名再拿IP，这里只返回主机名列表，由外层处理。
    """
    ns_names = []
    glue_ips = []

    # Authority 里的 NS 记录
    for rrset in resp.authority:
        if rrset.rdtype == rdatatype.NS:
            for rr in rrset:
                ns_names.append(str(rr.target).strip('.'))

    # Additional 里的 A/AAAA 作为 Glue
    for rrset in resp.additional:
        if rrset.rdtype in (rdatatype.A, rdatatype.AAAA):
            for rr in rrset:
                glue_ips.append(rr.address)

    return ns_names, glue_ips

def simple_a_lookup(hostname, fallback_servers):
    """
    为了给 NS 主机名找IP（当没有Glue时）。
    这里做一个非常小的递归查询（RD=1）到公共DNS，以便继续迭代。
    """
    r = dns.resolver.Resolver(configure=True)
    if fallback_servers:
        r.nameservers = fallback_servers
    try:
        ans = r.resolve(hostname, "A", raise_on_no_answer=True)
        return [rdata.address for rdata in ans]
    except Exception:
        return []

def rd0_iterative_query(name: str, qtype: str, timeout=2.0, udp_size=1232):
    """
    迭代查询（RD=0）：从根开始逐层跟随NS，直到拿到目标类型。
    返回最终的响应报文和发送该响应的服务器地址（ip, port）。
    """
    qname = dns.name.from_text(name)
    current_ns_ips = ROOT_SERVERS[:]
    last_resp = None
    last_server = None

    # 处理 CNAME 链：如果Answer里是CNAME，就把qname切换为别名指向的名字，继续
    while True:
        if not current_ns_ips:
            raise RuntimeError("No name servers to query.")

        ns_ip = random.choice(current_ns_ips)
        query = dns.message.make_query(qname, qtype)
        # 关闭递归（RD=0）
        query.flags &= ~dns.flags.RD

        try:
            resp = dns.query.udp(query, ns_ip, timeout=timeout, ignore_unexpected=True, udp_size=udp_size)
        except Exception:
            # 这个NS不通，换一个
            current_ns_ips.remove(ns_ip)
            continue

        last_resp = resp
        last_server = (ns_ip, 53)

        # 1) 先看是否已有目标类型的答案
        if resp.answer:
            # 先看是不是CNAME
            has_target = False
            next_cname = None
            for rrset in resp.answer:
                if rrset.rdtype == rdatatype.CNAME:
                    # 如果问的是A/AAAA等，而先给了CNAME，按CNAME跳转
                    next_cname = str(rrset[0].target).strip('.')
                if dns.rdatatype.to_text(rrset.rdtype).upper() == qtype.upper():
                    has_target = True
            if has_target:
                return last_resp, last_server  # 目标类型已拿到
            if next_cname:
                # 跟随CNAME
                qname = dns.name.from_text(next_cname)
                # 继续从同一组NS开始尝试（也可重新回根）
                continue

        # 2) 没有答案则读 Authority/Additional，获取下一跳 NS
        ns_names, glue_ips = extract_ns_ips(resp)

        # 优先使用 Glue 的 IP
        candidate_ips = glue_ips[:]

        # 没有 Glue 的话，先解析 NS 主机名的 A 记录拿到 IP（这里允许用公共DNS做一次小递归）
        if not candidate_ips and ns_names:
            # 这里可选用本机/公共DNS来解析NS名的A记录，这一步属于“辅助”
            # 以根或上游NS解析也行，实验里允许小幅简化
            for nsn in ns_names:
                ips = simple_a_lookup(nsn, fallback_servers=None)
                candidate_ips.extend(ips)

        if candidate_ips:
            # 更新下一跳
            current_ns_ips = candidate_ips
            continue

        # 实在没有线索：尝试回根重启一次，或直接失败
        current_ns_ips = ROOT_SERVERS[:]

def print_summary(resp: dns.message.Message, server_addr: tuple[str, int] | None):
    """
    打印题目要求的信息：答案/来源/AA标志等
    """
    flags = resp.flags
    aa = bool(flags & dns.flags.AA)
    ra = bool(flags & dns.flags.RA)
    rd = bool(flags & dns.flags.RD)

    print("=== DNS Response Summary ===")
    if server_addr:
        print(f"From server: {server_addr[0]}:{server_addr[1]}")
    print(f"ID: 0x{resp.id:04x}")
    print(f"Flags: RD={int(rd)} RA={int(ra)} AA={int(aa)}")
    print(f"Questions: {len(resp.question)}  Answers: {len(resp.answer)}  "
          f"Authority: {len(resp.authority)}  Additional: {len(resp.additional)}")

    if resp.answer:
        print("\nAnswer Section:")
        for rrset in resp.answer:
            print(rrset.to_text())

    if resp.authority:
        print("\nAuthority Section:")
        for rrset in resp.authority:
            print(rrset.to_text())

    if resp.additional:
        print("\nAdditional Section:")
        for rrset in resp.additional:
            print(rrset.to_text())
    print("============================\n")

def main():
    ap = argparse.ArgumentParser(description="Mini DNS client (RD=1 recursive / RD=0 iterative)")
    ap.add_argument("qname", help="domain name, e.g., www.sina.com.cn")
    ap.add_argument("-t", "--type", default="A", choices=sorted(SUPPORTED_TYPES), help="record type")
    ap.add_argument("--rd", type=int, choices=[0,1], default=1, help="1=recursive, 0=iterative")
    ap.add_argument("--server", help="recursive DNS server for RD=1 mode (e.g., 8.8.8.8)")
    args = ap.parse_args()

    qname = args.qname.rstrip(".")
    qtype = args.type.upper()

    if args.rd == 1:
        # 递归模式
        resp = rd1_recursive_query(qname, qtype, server=args.server)
        print_summary(resp, server_addr=None)  # 源地址由递归库隐藏，如需可抓包看
    else:
        # 迭代模式
        resp, server_addr = rd0_iterative_query(qname, qtype)
        print_summary(resp, server_addr=server_addr)

if __name__ == "__main__":
    main()
