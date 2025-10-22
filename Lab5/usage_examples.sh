#!/usr/bin/env bash

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

# Combined paraeters
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

# Test 8: Multi-step iterative query (may show multiple steps)
python dns_client.py www.microsoft.com -t A -m iterative

# Test 9: Another multi-step iterative query
python dns_client.py www.amazon.com -t A -m iterative

# Test 10: NS record iterative query (often shows multiple steps)
python dns_client.py microsoft.com -t NS -m iterative
# Test 11: Try a different domain for multi-step query
python dns_client.py www.apple.com -t A -m iterative

# Test 12: Try a subdomain that might need multiple steps
python dns_client.py mail.google.com -t A -m iterative

# Test 13: Try a different domain for multi-step query
python dns_client.py www.apple.com -t A -m iterative

# Test 14: Try a different domain for multi-step query
python dns_client.py www.apple.com -t A -m iterative

# Test 15: Try a different domain for multi-step query
python dns_client.py www.apple.com -t A -m iterative

# Test 16: Try a different domain for multi-step query
python dns_client.py www.apple.com -t A -m iterative

# Test 17: Try a different domain for multi-step query
python dns_client.py www.apple.com -t A -m iterative
