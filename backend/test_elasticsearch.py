#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to test Elasticsearch connection.
Run this to diagnose connection issues.
"""

import sys
import traceback
import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_elasticsearch_connection():
    es_url = "http://localhost:9200"
    print(f"Testing connection to Elasticsearch at {es_url}")
    print("-" * 60)
    
    try:
        # Try basic connection
        print("1. Creating Elasticsearch client...")
        es_module = __import__('elasticsearch')
        print(f"   Elasticsearch Python client version: {es_module.__version__}")
        
        # For ES 9.x client connecting to ES 8.x server, we need to set compatibility mode
        # The client defaults to version 9, but ES 8.11.1 only supports 7 or 8
        es = Elasticsearch(
            es_url,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
        # Override the default headers to use compatibility mode 8
        es._headers = {"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
        print("   ✓ Client created with compatibility mode 8")
        
        # Test ping using the newer API
        print("2. Testing ping...")
        try:
            # Use options() method for ES 8.x compatibility
            ping_result = es.options(request_timeout=10).ping()
            if ping_result:
                print("   ✓ Ping successful")
            else:
                print("   ✗ Ping returned False")
                # Try direct info() call as alternative
                print("   Trying alternative connection test...")
                try:
                    info = es.options(request_timeout=10).info()
                    print(f"   ✓ Alternative test successful - connected to {info.get('cluster_name', 'unknown')}")
                    ping_result = True
                except Exception as alt_e:
                    print(f"   ✗ Alternative test also failed: {str(alt_e)}")
                    return False
        except Exception as ping_error:
            print(f"   ✗ Ping error: {str(ping_error)}")
            print(f"   Error type: {type(ping_error).__name__}")
            # Try direct info() call as alternative
            print("   Trying alternative connection test...")
            try:
                info = es.options(request_timeout=10).info()
                print(f"   ✓ Alternative test successful - connected to {info.get('cluster_name', 'unknown')}")
                ping_result = True
            except Exception as alt_e:
                print(f"   ✗ Alternative test also failed: {str(alt_e)}")
                return False
        
        if not ping_result:
            return False
        
        # Get cluster info
        print("3. Getting cluster info...")
        info = es.options(request_timeout=10).info()
        print(f"   ✓ Connected to cluster: {info.get('cluster_name', 'unknown')}")
        print(f"   ✓ Elasticsearch version: {info.get('version', {}).get('number', 'unknown')}")
        
        # List indices
        print("4. Listing indices...")
        indices = es.options(request_timeout=10).indices.get_alias(index="*")
        print(f"   ✓ Found {len(indices)} indices")
        if indices:
            print(f"   Indices: {', '.join(list(indices.keys())[:5])}")
        
        print("-" * 60)
        print("✓ All tests passed! Elasticsearch is accessible.")
        return True
        
    except ESConnectionError as e:
        print(f"   ✗ Connection Error: {str(e)}")
        print("\nPossible causes:")
        print("  - Elasticsearch is not running")
        print("  - Wrong URL/port")
        print("  - Network/firewall blocking connection")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_elasticsearch_connection()
    sys.exit(0 if success else 1)
