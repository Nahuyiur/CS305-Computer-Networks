#!/usr/bin/env python3
"""
DNS查询工具 - 简化版
根据练习要求实现基本功能
"""

import argparse
import dns.resolver
import dns.query
import dns.message
import dns.name
import dns.rdatatype

def query_with_resolver(domain, query_type, dns_server='8.8.8.8'):
    """使用dns.resolver查询"""
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        
        type_map = {'A': dns.rdatatype.A, 'AAAA': dns.rdatatype.AAAA, 
                   'CNAME': dns.rdatatype.CNAME, 'NS': dns.rdatatype.NS, 'MX': dns.rdatatype.MX}
        
        answer = resolver.resolve(domain, type_map.get(query_type.upper(), dns.rdatatype.A))
        
        print(f"Querying {domain} ({query_type}) from {dns_server}")
        print("-" * 40)
        
        for rdata in answer:
            print(f"{domain} {answer.rrset.ttl} {query_type} {rdata}")
        
        print(f"Authoritative: {'Yes' if answer.response.flags & dns.flags.AA else 'No'}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def query_with_socket(domain, query_type, dns_server='8.8.8.8', rd_flag=1):
    """使用UDP socket查询"""
    try:
        qname = dns.name.from_text(domain)
        type_map = {'A': dns.rdatatype.A, 'AAAA': dns.rdatatype.AAAA, 
                   'CNAME': dns.rdatatype.CNAME, 'NS': dns.rdatatype.NS, 'MX': dns.rdatatype.MX}
        
        query = dns.message.make_query(qname, type_map.get(query_type.upper(), dns.rdatatype.A))
        
        if rd_flag == 0:
            query.flags &= ~dns.flags.RD
        else:
            query.flags |= dns.flags.RD
        
        response = dns.query.udp(query, dns_server, timeout=5)
        
        print(f"Querying {domain} ({query_type}) from {dns_server}")
        print(f"RD flag: {rd_flag}")
        print("-" * 40)
        
        if len(response.answer) > 0:
            for rrset in response.answer:
                for rdata in rrset:
                    print(f"{rrset.name} {rrset.ttl} {dns.rdatatype.to_text(rrset.rdtype)} {rdata}")
        else:
            print("No answer records found")
        
        print(f"Response Code: {dns.rcode.to_text(response.rcode())}")
        print(f"Authoritative: {'Yes' if response.flags & dns.flags.AA else 'No'}")
        
        if response.flags & dns.flags.AA:
            print("-> This is an authoritative answer")
        else:
            print("-> This is a non-authoritative answer")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def iterative_query(domain, query_type):
    """迭代查询"""
    root_servers = ['198.41.0.4', '199.9.14.201', '192.33.4.12', '199.7.91.13', 
                   '192.203.230.10', '192.5.5.241', '192.112.36.4', '198.97.190.53',
                   '192.36.148.17', '192.58.128.30', '193.0.14.129', '199.7.83.42', '202.12.27.33']
    
    current_servers = root_servers
    print(f"Iterative query for {domain} ({query_type})")
    print("=" * 50)
    
    for step in range(3):  # 减少步数
        print(f"\nStep {step + 1}: Querying {len(current_servers)} server(s)")
        
        for server in current_servers[:3]:  # 只尝试前3个服务器
            try:
                qname = dns.name.from_text(domain)
                type_map = {'A': dns.rdatatype.A, 'AAAA': dns.rdatatype.AAAA, 
                           'CNAME': dns.rdatatype.CNAME, 'NS': dns.rdatatype.NS, 'MX': dns.rdatatype.MX}
                
                query = dns.message.make_query(qname, type_map.get(query_type.upper(), dns.rdatatype.A))
                query.flags &= ~dns.flags.RD  # RD=0
                
                response = dns.query.udp(query, server, timeout=3)
                
                print(f"  {server}: {dns.rcode.to_text(response.rcode())} | Auth: {'Yes' if response.flags & dns.flags.AA else 'No'} | Answers: {len(response.answer)}")
                
                if len(response.answer) > 0:
                    print(f"\n[SUCCESS] Found answer!")
                    for rrset in response.answer:
                        for rdata in rrset:
                            print(f"  {rrset.name} {rrset.ttl} {dns.rdatatype.to_text(rrset.rdtype)} {rdata}")
                    return True
                
                # 获取下一个服务器
                next_servers = []
                for rrset in response.authority:
                    if rrset.rdtype == dns.rdatatype.NS:
                        for additional in response.additional:
                            if additional.rdtype == dns.rdatatype.A:
                                for rdata in additional:
                                    if str(rdata) not in next_servers:
                                        next_servers.append(str(rdata))
                
                if next_servers:
                    current_servers = next_servers[:3]  # 限制数量
                    print(f"  Next servers: {current_servers}")
                    break
                    
            except Exception as e:
                print(f"  {server}: Error - {e}")
                continue
    
    print("\n[FAILED] Iterative query failed")
    return False

def main():
    parser = argparse.ArgumentParser(description='DNS Query Tool')
    parser.add_argument('domain', help='Domain name to query')
    parser.add_argument('-t', '--type', default='A', choices=['A', 'AAAA', 'CNAME', 'NS', 'MX'])
    parser.add_argument('-s', '--server', default='8.8.8.8')
    parser.add_argument('--no-recursion', action='store_true')
    parser.add_argument('--iterative', action='store_true')
    parser.add_argument('--method', choices=['resolver', 'socket'], default='socket')
    
    args = parser.parse_args()
    rd_flag = 0 if args.no_recursion else 1
    
    # 如果RD=0，强制使用迭代查询
    if args.no_recursion or args.iterative:
        iterative_query(args.domain, args.type)
    elif args.method == 'resolver':
        query_with_resolver(args.domain, args.type, args.server)
    else:
        query_with_socket(args.domain, args.type, args.server, rd_flag)

if __name__ == '__main__':
    main()
