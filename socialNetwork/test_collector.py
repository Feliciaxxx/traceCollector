#!/usr/bin/env python3
"""
直接向我们的collector发送测试traces
"""

import requests
import json
import time

def send_test_trace():
    """发送一个测试trace到我们的collector"""
    
    # OTLP HTTP端点
    collector_url = "http://127.0.0.1:8326/v1/traces"
    
    # 构造一个简单的trace
    trace_data = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {
                                "stringValue": "test-service"
                            }
                        }
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {
                            "name": "test-tracer"
                        },
                        "spans": [
                            {
                                "traceId": "0102030405060708090a0b0c0d0e0f10",
                                "spanId": "1112131415161718",
                                "name": "test-span",
                                "kind": 1,
                                "startTimeUnixNano": str(int(time.time() * 1000000000)),
                                "endTimeUnixNano": str(int(time.time() * 1000000000) + 1000000000),
                                "attributes": [
                                    {
                                        "key": "test.key",
                                        "value": {
                                            "stringValue": "test-value"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("发送测试trace到collector...")
        response = requests.post(collector_url, json=trace_data, headers=headers)
        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 测试trace发送成功！")
        else:
            print(f"❌ 发送失败: {response.text}")
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def main():
    print("=" * 50)
    print("测试Collector连接性")
    print("=" * 50)
    
    # 发送多个测试traces
    for i in range(5):
        print(f"\n发送第 {i+1} 个测试trace...")
        send_test_trace()
        time.sleep(1)
    
    print("\n测试完成！请检查collector日志...")

if __name__ == "__main__":
    main()
