#!/usr/bin/env python3
import requests
import json
import time
import random

# OTLP HTTP endpoint for our custom collector
COLLECTOR_URL = "http://localhost:8326/v1/traces"

def generate_test_trace(trace_id, span_count=5):
    """生成测试trace数据"""
    spans = []
    base_time = int(time.time() * 1_000_000_000)  # nanoseconds
    
    for i in range(span_count):
        span_id = f"{i+1:016x}"
        
        # 添加一些随机的latency和status来让遗传算法有更多样的数据
        duration = random.randint(10_000_000, 500_000_000)  # 10ms to 500ms
        status_code = random.choice([0, 0, 0, 0, 1, 2])  # 大部分成功，少部分错误
        
        span = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": f"test-operation-{i+1}",
            "kind": 1,
            "startTimeUnixNano": str(base_time + i * 1_000_000),
            "endTimeUnixNano": str(base_time + i * 1_000_000 + duration),
            "attributes": [
                {"key": "service.name", "value": {"stringValue": f"test-service-{i+1}"}},
                {"key": "latency.ms", "value": {"doubleValue": duration / 1_000_000}},
                {"key": "error.rate", "value": {"doubleValue": random.uniform(0.01, 0.1)}}
            ],
            "status": {"code": status_code}
        }
        
        # 只有非root spans才设置parentSpanId
        if i > 0:
            span["parentSpanId"] = f"{i:016x}"
            
        spans.append(span)
    
    return {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "test-microservice"}},
                    {"key": "service.version", "value": {"stringValue": "1.0.0"}}
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "test-scope"},
                "spans": spans
            }]
        }]
    }

def send_traces():
    """发送多个test traces到collector"""
    print("发送测试traces到自定义collector...")
    
    for trace_num in range(10):  # 发送10个traces
        trace_id = f"{trace_num+1:032x}"
        span_count = random.randint(3, 8)  # 每个trace 3-8个spans
        
        trace_data = generate_test_trace(trace_id, span_count)
        
        try:
            response = requests.post(
                COLLECTOR_URL,
                json=trace_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"Trace {trace_num+1}: {response.status_code} - {span_count} spans")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Error sending trace {trace_num+1}: {e}")
        
        time.sleep(0.5)  # 500ms间隔

if __name__ == "__main__":
    send_traces()
    print("完成！检查collector日志查看遗传算法处理结果...")
