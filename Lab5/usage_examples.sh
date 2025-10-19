#!/usr/bin/env bash
# DNS Client Usage Examples

# Basic A record query (recursive)
python dns_client.py www.baidu.com

# Specify query type
python dns_client.py www.baidu.com -t A
python dns_client.py baidu.com -t NS
python dns_client.py gmail.com -t MX
python dns_client.py www.github.com -t CNAME

# Specify query mode
python dns_client.py www.baidu.com -m recursive
python dns_client.py www.baidu.com -m iterative

# Specify DNS server
python dns_client.py www.baidu.com -s 8.8.8.8
python dns_client.py www.baidu.com -s 1.1.1.1

# Combined parameters
python dns_client.py baidu.com -t NS -m iterative
python dns_client.py gmail.com -t MX -s 8.8.8.8
python dns_client.py www.github.com -t CNAME -m recursive

# Show help
python dns_client.py -h

# Test 1: A record recursive query
python dns_client.py www.baidu.com

# Test 2: A record iterative query
python dns_client.py www.baidu.com -m iterative

# Test 3: NS record query
python dns_client.py baidu.com -t NS

# Test 4: MX record query
python dns_client.py gmail.com -t MX

# Test 5: CNAME record query
python dns_client.py www.github.com -t CNAME

# Test 6: Combined test (NS with iterative)
python dns_client.py google.com -t NS -m iterative

# Test 7: Different DNS server
python dns_client.py www.sina.com.cn -t A -s 1.1.1.1