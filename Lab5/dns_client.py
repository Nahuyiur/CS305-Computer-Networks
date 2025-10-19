import socket
import struct
import random
import time

class DNSClient:
    def __init__(self):
        # DNS查询类型映射
        self.query_types = {
            'A': 1,      # IPv4地址
            'AAAA': 28,  # IPv6地址
            'CNAME': 5,  # 别名
            'NS': 2,     # 域名服务器
            'MX': 15     # 邮件交换
        }
        
        # 根DNS服务器列表
        self.root_servers = [
            '198.41.0.4',      # a.root-servers.net
            '199.9.14.201',    # b.root-servers.net
            '192.33.4.12',     # c.root-servers.net
            '199.7.91.13',     # d.root-servers.net
            '192.203.230.10',  # e.root-servers.net
            '192.5.5.241',     # f.root-servers.net
            '192.112.36.4',    # g.root-servers.net
            '198.97.190.53',   # h.root-servers.net
            '192.36.148.17',   # i.root-servers.net
            '192.58.128.30',  # j.root-servers.net
            '193.0.14.129',    # k.root-servers.net
            '199.7.83.42',     # l.root-servers.net
            '202.12.27.33'     # m.root-servers.net
        ]
    
    def encode_domain_name(self, domain):
        """将域名编码为DNS格式"""
        parts = domain.split('.')
        encoded = b''
        for part in parts:
            encoded += struct.pack('B', len(part)) + part.encode()
        encoded += b'\x00' 
        return encoded
    
    def decode_domain_name(self, data, offset):
        """解码DNS格式的域名"""
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
        """创建DNS查询包"""
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
        qclass = 1  # IN (Internet)
        
        query = struct.pack('!HH', qtype, qclass)
        
        return header + qname + query, transaction_id
    
    def parse_dns_response(self, data):
        """解析DNS响应"""
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
        """解析资源记录"""
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
        
        if rtype == 1:  # A记录
            if len(rdata) == 4:
                record['ip'] = socket.inet_ntoa(rdata)
        elif rtype == 28:  # AAAA记录
            if len(rdata) == 16:
                record['ip'] = socket.inet_ntop(socket.AF_INET6, rdata)
        elif rtype == 5:  # CNAME记录
            cname, _ = self.decode_domain_name(data, offset - rdlength)
            record['cname'] = '.'.join(cname)
        elif rtype == 2:  # NS记录
            ns, _ = self.decode_domain_name(data, offset - rdlength)
            record['ns'] = '.'.join(ns)
        elif rtype == 15:  # MX记录
            if len(rdata) >= 2:
                preference = struct.unpack('!H', rdata[:2])[0]
                mx, _ = self.decode_domain_name(data, offset - rdlength + 2)
                record['preference'] = preference
                record['mx'] = '.'.join(mx)
        
        return record
    
    def send_query(self, server_ip, query_data, timeout=5):
        """Send DNS query"""
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
        """Recursive query (RD=1)"""
        print(f"\n=== Recursive Query {domain} ({query_type}) ===")
        print(f"Using DNS server: {dns_server}")
        
        query_data, transaction_id = self.create_dns_query(domain, query_type, rd_flag=1)
        response_data = self.send_query(dns_server, query_data)
        
        if not response_data:
            print("Query failed")
            return None
        
        response = self.parse_dns_response(response_data)
        if not response:
            print("Failed to parse response")
            return None
        
        self.display_response(response, domain, query_type)
        return response
    
    def iterative_query(self, domain, query_type):
        """Iterative query (RD=0)"""
        print(f"\n=== Iterative Query {domain} ({query_type}) ===")
        
        current_servers = self.root_servers.copy()
        query_data, transaction_id = self.create_dns_query(domain, query_type, rd_flag=0)
        
        for step in range(10):  # Maximum 10 steps
            print(f"\n--- Step {step + 1} ---")
            
            for server in current_servers:
                print(f"Querying server: {server}")
                response_data = self.send_query(server, query_data)
                
                if not response_data:
                    continue
                
                response = self.parse_dns_response(response_data)
                if not response:
                    continue
                
                print(f"Response code: {response['rcode']}")
                print(f"Authoritative answer: {'Yes' if response['aa'] else 'No'}")
                
                # If there are answer records
                if response['answer_records']:
                    print("Found answer records:")
                    for record in response['answer_records']:
                        self.display_record(record)
                    return response
                
                # If no answer records but no authority records either, 
                # this might be a direct answer from root server
                if not response['authority_records'] and not response['answer_records']:
                    print("No records found")
                    return response
                
                # If there are authority records, use authoritative servers
                if response['authority_records']:
                    print("Authority records:")
                    for record in response['authority_records']:
                        if record['type'] == 2:  # NS record
                            print(f"  NS: {record['ns']}")
                    
                    # Find corresponding A records
                    current_servers = []
                    for record in response['additional_records']:
                        if record['type'] == 1:  # A record
                            current_servers.append(record['ip'])
                            print(f"  Server IP: {record['ip']}")
                    
                    if current_servers:
                        break
                    else:
                        # If no A records, need to query NS record IPs
                        print("Need to query NS record IP addresses")
                        for ns_record in response['authority_records']:
                            if ns_record['type'] == 2:
                                ns_query = self.iterative_query(ns_record['ns'], 'A')
                                if ns_query and ns_query['answer_records']:
                                    for ans in ns_query['answer_records']:
                                        if ans['type'] == 1:
                                            current_servers.append(ans['ip'])
                        break
                
                # If no authority records, continue with root servers
                if not response['authority_records']:
                    break
        
        print("Iterative query timeout")
        return None
    
    def display_record(self, record):
        """Display resource record"""
        if record['type'] == 1:  # A record
            print(f"  A: {record['name']} -> {record['ip']}")
        elif record['type'] == 28:  # AAAA record
            print(f"  AAAA: {record['name']} -> {record['ip']}")
        elif record['type'] == 5:  # CNAME record
            print(f"  CNAME: {record['name']} -> {record['cname']}")
        elif record['type'] == 2:  # NS record
            print(f"  NS: {record['name']} -> {record['ns']}")
        elif record['type'] == 15:  # MX record
            print(f"  MX: {record['name']} -> {record['mx']} (Priority: {record['preference']})")
    
    def display_response(self, response, domain, query_type):
        """Display DNS response"""
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
    """Main function"""
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
        # Interactive mode
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
        # Command line argument mode
        print(f"DNS Query: {args.domain} ({args.type})")
        print(f"Query mode: {args.mode}")
        
        if args.mode == 'recursive':
            client.recursive_query(args.domain, args.type, args.server)
        else:
            client.iterative_query(args.domain, args.type)

if __name__ == "__main__":
    main()
