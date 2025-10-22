#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS客户端实现
支持A、AAAA、CNAME、NS、MX查询类型
支持递归查询(RD=1)和迭代查询(RD=0)
"""

import socket
import struct
import random
import time
import dns.resolver
import dns.query
import dns.message
import dns.name
import dns.rdatatype

class DNSClient:
    def __init__(self):
        self.query_types = {
            'A': 1,
            'AAAA': 28,
            'CNAME': 5,
            'NS': 2,
            'MX': 15
        }
        
        self.root_servers = [
            '198.41.0.4',
            '199.9.14.201',
            '192.33.4.12',
            '199.7.91.13',
            '192.203.230.10',
            '192.5.5.241',
            '192.112.36.4',
            '198.97.190.53',
            '192.36.148.17',
            '192.58.128.30',
            '193.0.14.129',
            '199.7.83.42',
            '202.12.27.33'
        ]
    
    def encode_domain_name(self, domain):
        parts = domain.split('.')
        encoded = b''
        for part in parts:
            encoded += struct.pack('B', len(part)) + part.encode()
        encoded += b'\x00'
        return encoded
    
    def decode_domain_name(self, data, offset):
        labels = []
        original_offset = offset
        
        while True:
            length = data[offset]
            offset += 1
            
            if length == 0:
                break
            elif length & 0xC0 == 0xC0:
                pointer = ((length & 0x3F) << 8) | data[offset]
                offset += 1
                compressed_labels, _ = self.decode_domain_name(data, pointer)
                labels.extend(compressed_labels)
                break
            else:
                label = data[offset:offset + length].decode()
                labels.append(label)
                offset += length
        
        return labels, offset
    
    def create_dns_query(self, domain, query_type, rd_flag=1):
        transaction_id = random.randint(1, 65535)
        flags = 0x0100 if rd_flag else 0x0000
        questions = 1
        answers = 0
        authority = 0
        additional = 0
        
        header = struct.pack('!HHHHHH', 
                           transaction_id, flags, questions, 
                           answers, authority, additional)
        
        qname = self.encode_domain_name(domain)
        qtype = self.query_types[query_type]
        qclass = 1
        
        query = struct.pack('!HH', qtype, qclass)
        
        return header + qname + query, transaction_id
    
    def parse_dns_response(self, data):
        if len(data) < 12:
            return None
        
        transaction_id, flags, questions, answers, authority, additional = \
            struct.unpack('!HHHHHH', data[:12])
        
        response = {
            'transaction_id': transaction_id,
            'flags': flags,
            'questions': questions,
            'answers': answers,
            'authority': authority,
            'additional': additional,
            'aa': bool(flags & 0x0400),
            'rd': bool(flags & 0x0100),
            'ra': bool(flags & 0x0080),
            'rcode': flags & 0x000F,
            'answer_records': [],
            'authority_records': [],
            'additional_records': []
        }
        
        offset = 12
        
        for _ in range(questions):
            _, offset = self.decode_domain_name(data, offset)
            offset += 4
        
        for _ in range(answers):
            record = self.parse_resource_record(data, offset)
            response['answer_records'].append(record)
            offset = record['next_offset']
        
        for _ in range(authority):
            record = self.parse_resource_record(data, offset)
            response['authority_records'].append(record)
            offset = record['next_offset']
        
        for _ in range(additional):
            record = self.parse_resource_record(data, offset)
            response['additional_records'].append(record)
            offset = record['next_offset']
        
        return response
    
    def parse_resource_record(self, data, offset):
        name, offset = self.decode_domain_name(data, offset)
        
        if offset + 10 > len(data):
            return {'next_offset': len(data)}
        
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        
        record = {
            'name': '.'.join(name),
            'type': rtype,
            'class': rclass,
            'ttl': ttl,
            'data': rdata,
            'next_offset': offset
        }
        
        if rtype == 1:
            if len(rdata) == 4:
                record['ip'] = socket.inet_ntoa(rdata)
        elif rtype == 28:
            if len(rdata) == 16:
                record['ip'] = socket.inet_ntop(socket.AF_INET6, rdata)
        elif rtype == 5:
            cname, _ = self.decode_domain_name(data, offset - rdlength)
            record['cname'] = '.'.join(cname)
        elif rtype == 2:
            ns, _ = self.decode_domain_name(data, offset - rdlength)
            record['ns'] = '.'.join(ns)
        elif rtype == 15:
            if len(rdata) >= 2:
                preference = struct.unpack('!H', rdata[:2])[0]
                mx, _ = self.decode_domain_name(data, offset - rdlength + 2)
                record['preference'] = preference
                record['mx'] = '.'.join(mx)
        
        return record
    
    def send_query(self, server_ip, query_data, timeout=5):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(query_data, (server_ip, 53))
            response, _ = sock.recvfrom(512)
            sock.close()
            return response
        except Exception as e:
            print(f"Query to {server_ip} failed: {e}")
            return None
    
    def recursive_query(self, domain, query_type, dns_server='8.8.8.8'):
        print(f"\n=== Recursive Query {domain} ({query_type}) ===")
        print(f"Using DNS server: {dns_server}")
        
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            
            type_map = {'A': dns.rdatatype.A, 'AAAA': dns.rdatatype.AAAA, 
                       'CNAME': dns.rdatatype.CNAME, 'NS': dns.rdatatype.NS, 'MX': dns.rdatatype.MX}
            
            answer = resolver.resolve(domain, type_map.get(query_type.upper(), dns.rdatatype.A))
            
            print(f"Query domain: {domain}")
            print(f"Query type: {query_type}")
            print(f"Response code: 0")
            print(f"Authoritative answer: {'Yes' if answer.response.flags & dns.flags.AA else 'No'}")
            print(f"Recursion desired: Yes")
            print(f"Recursion available: Yes")
            
            if answer:
                print("\nAnswer records:")
                for rdata in answer:
                    print(f"  {query_type}: {domain} -> {rdata}")
            
            return True
            
        except Exception as e:
            print(f"Query failed: {e}")
            return False
    
    def iterative_query(self, domain, query_type):
        print(f"\n=== Iterative Query {domain} ({query_type}) ===")
        
        current_servers = self.root_servers
        print(f"Iterative query for {domain} ({query_type})")
        print("=" * 50)
        
        for step in range(5):
            print(f"\nStep {step + 1}: Querying {len(current_servers)} server(s)")
            
            for server in current_servers[:3]:
                try:
                    qname = dns.name.from_text(domain)
                    type_map = {'A': dns.rdatatype.A, 'AAAA': dns.rdatatype.AAAA, 
                               'CNAME': dns.rdatatype.CNAME, 'NS': dns.rdatatype.NS, 'MX': dns.rdatatype.MX}
                    
                    query = dns.message.make_query(qname, type_map.get(query_type.upper(), dns.rdatatype.A))
                    query.flags &= ~dns.flags.RD
                    
                    response = dns.query.udp(query, server, timeout=3)
                    
                    print(f"  {server}: {dns.rcode.to_text(response.rcode())} | Auth: {'Yes' if response.flags & dns.flags.AA else 'No'} | Answers: {len(response.answer)}")
                    
                    if len(response.answer) > 0:
                        print(f"\n[SUCCESS] Found answer!")
                        for rrset in response.answer:
                            for rdata in rrset:
                                print(f"  {rrset.name} {rrset.ttl} {dns.rdatatype.to_text(rrset.rdtype)} {rdata}")
                        return True
                    
                    next_servers = []
                    for rrset in response.authority:
                        if rrset.rdtype == dns.rdatatype.NS:
                            for additional in response.additional:
                                if additional.rdtype == dns.rdatatype.A:
                                    for rdata in additional:
                                        if str(rdata) not in next_servers:
                                            next_servers.append(str(rdata))
                    
                    if next_servers:
                        current_servers = next_servers[:3]
                        print(f"  Next servers: {current_servers}")
                        break
                        
                except Exception as e:
                    print(f"  {server}: Error - {e}")
                    continue
        
        print("\n[FAILED] Iterative query failed")
        return False
    
    def display_record(self, record):
        if record['type'] == 1:
            print(f"  A: {record['name']} -> {record['ip']}")
        elif record['type'] == 28:
            print(f"  AAAA: {record['name']} -> {record['ip']}")
        elif record['type'] == 5:
            print(f"  CNAME: {record['name']} -> {record['cname']}")
        elif record['type'] == 2:
            print(f"  NS: {record['name']} -> {record['ns']}")
        elif record['type'] == 15:
            print(f"  MX: {record['name']} -> {record['mx']} (Priority: {record['preference']})")
    
    def display_response(self, response, domain, query_type):
        print(f"\nQuery domain: {domain}")
        print(f"Query type: {query_type}")
        print(f"Transaction ID: {response['transaction_id']}")
        print(f"Response code: {response['rcode']}")
        print(f"Authoritative answer: {'Yes' if response['aa'] else 'No'}")
        print(f"Recursion desired: {'Yes' if response['rd'] else 'No'}")
        print(f"Recursion available: {'Yes' if response['ra'] else 'No'}")
        
        if response['answer_records']:
            print("\nAnswer records:")
            for record in response['answer_records']:
                self.display_record(record)
        
        if response['authority_records']:
            print("\nAuthority records:")
            for record in response['authority_records']:
                self.display_record(record)
        
        if response['additional_records']:
            print("\nAdditional records:")
            for record in response['additional_records']:
                self.display_record(record)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='DNS Client - Supports A, AAAA, CNAME, NS, MX queries')
    parser.add_argument('domain', help='Domain to query')
    parser.add_argument('-t', '--type', choices=['A', 'AAAA', 'CNAME', 'NS', 'MX'], 
                       default='A', help='Query type (default: A)')
    parser.add_argument('-m', '--mode', choices=['recursive', 'iterative'], 
                       default='recursive', help='Query mode (default: recursive)')
    parser.add_argument('-s', '--server', default='8.8.8.8', 
                       help='DNS server for recursive queries (default: 8.8.8.8)')
    parser.add_argument('--interactive', action='store_true', 
                       help='Interactive mode')
    
    args = parser.parse_args()
    
    client = DNSClient()
    
    if args.interactive:
        print("DNS Client - Interactive Mode")
        print("Supported query types: A, AAAA, CNAME, NS, MX")
        print("Type 'quit' to exit")
        
        while True:
            print("\n" + "="*50)
            domain = input("Enter domain to query: ").strip()
            
            if domain.lower() == 'quit':
                break
            
            if not domain:
                continue
            
            print("\nQuery types:")
            print("1. A (IPv4 address)")
            print("2. AAAA (IPv6 address)")
            print("3. CNAME (Canonical name)")
            print("4. NS (Name server)")
            print("5. MX (Mail exchange)")
            
            choice = input("Select query type (1-5): ").strip()
            
            query_type_map = {
                '1': 'A',
                '2': 'AAAA', 
                '3': 'CNAME',
                '4': 'NS',
                '5': 'MX'
            }
            
            if choice not in query_type_map:
                print("Invalid choice")
                continue
            
            query_type = query_type_map[choice]
            
            print("\nQuery modes:")
            print("1. Recursive query (RD=1)")
            print("2. Iterative query (RD=0)")
            
            mode = input("Select query mode (1-2): ").strip()
            
            if mode == '1':
                client.recursive_query(domain, query_type)
            elif mode == '2':
                client.iterative_query(domain, query_type)
            else:
                print("Invalid choice")
    else:
        print(f"DNS Query: {args.domain} ({args.type})")
        print(f"Query mode: {args.mode}")
        
        if args.mode == 'recursive':
            client.recursive_query(args.domain, args.type, args.server)
        else:
            client.iterative_query(args.domain, args.type)

if __name__ == "__main__":
    main()