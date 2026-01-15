#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Client Test Script
"""

from dns_client import DNSClient

def test_dns_client():
    """Test DNS client functionality"""
    client = DNSClient()
    
    # Test cases
    test_cases = [
        {
            'domain': 'www.baidu.com',
            'query_type': 'A',
            'description': 'Baidu A record query'
        },
        {
            'domain': 'baidu.com', 
            'query_type': 'NS',
            'description': 'Baidu NS record query'
        },
        {
            'domain': 'gmail.com',
            'query_type': 'MX', 
            'description': 'Gmail MX record query'
        },
        {
            'domain': 'www.github.com',
            'query_type': 'CNAME',
            'description': 'GitHub CNAME record query'
        }
    ]
    
    print("=" * 60)
    print("DNS Client Test")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Domain: {test_case['domain']}")
        print(f"Query type: {test_case['query_type']}")
        
        # Test recursive query
        print("\n--- Recursive Query Test ---")
        try:
            response = client.recursive_query(
                test_case['domain'], 
                test_case['query_type']
            )
            if response:
                print("✅ Recursive query successful")
            else:
                print("❌ Recursive query failed")
        except Exception as e:
            print(f"❌ Recursive query error: {e}")
        
        # Test iterative query
        print("\n--- Iterative Query Test ---")
        try:
            response = client.iterative_query(
                test_case['domain'],
                test_case['query_type']
            )
            if response:
                print("✅ Iterative query successful")
            else:
                print("❌ Iterative query failed")
        except Exception as e:
            print(f"❌ Iterative query error: {e}")
        
        print("\n" + "-" * 40)
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_dns_client()
