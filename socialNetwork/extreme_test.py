#!/usr/bin/env python3
import requests
import json
import time
import random
import threading
import concurrent.futures

# OTLP HTTP endpoint for our custom collector
COLLECTOR_URL = "http://localhost:8326/v1/traces"

def generate_extreme_trace(trace_id, span_count=15):
    """生成极端复杂的测试trace数据来强制触发高级遗传算法"""
    spans = []
    base_time = int(time.time() * 1_000_000_000)  # nanoseconds
    
    # 极端多样化的服务类型
    service_types = [
        "auth", "payment", "inventory", "recommendation", "social-graph", 
        "timeline", "notification", "analytics", "billing", "fraud-detection",
        "content-delivery", "search", "ml-inference", "data-pipeline",
        "user-profile", "messaging", "file-storage", "video-processing",
        "real-time-chat", "recommendation-engine", "ad-targeting"
    ]
    
    # 极端的错误率分布
    error_rates = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.8]
    
    # 极端的延迟分布
    latencies = [
        (1_000_000, 10_000_000),      # 超快 1-10ms
        (10_000_000, 50_000_000),     # 快速 10-50ms
        (50_000_000, 200_000_000),    # 中等 50-200ms  
        (200_000_000, 1_000_000_000), # 慢速 200ms-1s
        (1_000_000_000, 5_000_000_000), # 很慢 1-5s
        (5_000_000_000, 15_000_000_000) # 极慢 5-15s
    ]
    
    for i in range(span_count):
        span_id = f"{i+1:016x}"
        service_type = random.choice(service_types)
        error_rate = random.choice(error_rates)
        latency_range = random.choice(latencies)
        duration = random.randint(latency_range[0], latency_range[1])
        
        # 极端的状态码分布
        if error_rate > 0.3:
            status_code = random.choice([1, 2, 2, 2])  # 高错误率
        elif error_rate > 0.1:
            status_code = random.choice([0, 0, 1, 2])  # 中错误率
        else:
            status_code = random.choice([0, 0, 0, 0, 0, 0, 0, 1])  # 低错误率
        
        span = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": f"{service_type}-extreme-operation-{i+1}",
            "kind": random.choice([1, 2, 3, 4, 5]),  # 所有span类型
            "startTimeUnixNano": str(base_time + i * 1_000_000),
            "endTimeUnixNano": str(base_time + i * 1_000_000 + duration),
            "attributes": [
                {"key": "service.name", "value": {"stringValue": f"{service_type}-extreme-service"}},
                {"key": "latency.ms", "value": {"doubleValue": duration / 1_000_000}},
                {"key": "error.rate", "value": {"doubleValue": error_rate}},
                {"key": "throughput", "value": {"doubleValue": random.uniform(1, 50000)}},
                {"key": "cpu.usage", "value": {"doubleValue": random.uniform(0.01, 0.99)}},
                {"key": "memory.usage", "value": {"doubleValue": random.uniform(0.05, 0.95)}},
                {"key": "operation.complexity", "value": {"intValue": random.randint(1, 20)}},
                {"key": "data.size.mb", "value": {"doubleValue": random.uniform(0.1, 1000)}},
                {"key": "network.latency.ms", "value": {"doubleValue": random.uniform(1, 500)}},
                {"key": "db.connections", "value": {"intValue": random.randint(1, 100)}},
                {"key": "cache.hit.ratio", "value": {"doubleValue": random.uniform(0.1, 0.9)}},
                {"key": "concurrent.users", "value": {"intValue": random.randint(1, 10000)}},
                {"key": "request.size.kb", "value": {"doubleValue": random.uniform(0.5, 10000)}},
                {"key": "response.size.kb", "value": {"doubleValue": random.uniform(0.1, 50000)}},
                {"key": "security.threat.level", "value": {"intValue": random.randint(0, 5)}}
            ],
            "status": {"code": status_code}
        }
        
        # 复杂的父子关系
        if i > 0:
            if i == 1:
                span["parentSpanId"] = f"{1:016x}"
            elif i <= 3:
                span["parentSpanId"] = f"{random.randint(1, i):016x}"
            else:
                span["parentSpanId"] = f"{random.randint(max(1, i-3), i):016x}"
            
        spans.append(span)
    
    return {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": f"extreme-microservice-{random.randint(1,10)}"}},
                    {"key": "service.version", "value": {"stringValue": f"3.{random.randint(0,9)}.{random.randint(0,9)}"}},
                    {"key": "deployment.environment", "value": {"stringValue": random.choice(["prod", "staging", "dev", "test", "canary"])}},
                    {"key": "datacenter", "value": {"stringValue": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"])}},
                    {"key": "cluster.id", "value": {"stringValue": f"cluster-{random.randint(1,20)}"}},
                    {"key": "node.id", "value": {"stringValue": f"node-{random.randint(1,100)}"}}
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "extreme-test-scope-v2"},
                "spans": spans
            }]
        }]
    }

def extreme_stress_test():
    """极端压力测试，强制触发高级遗传算法"""
    print("🧬🔥 开始极端压力测试 - 强制触发高级遗传算法...")
    print("目标：产生足够复杂的数据使简单算法失败，从而触发高级算法")
    print("="*80)
    
    batch_size = 8  # 每批8个traces以快速填满buffer
    total_batches = 50  # 总共400个极端复杂的traces
    
    def send_extreme_batch(batch_id):
        print(f"🚀 批次 {batch_id}: 发送极端复杂traces...")
        
        for trace_num in range(batch_size):
            trace_id = f"{batch_id:04x}{trace_num+1:028x}"
            span_count = random.randint(10, 20)  # 大量spans增加复杂性
            
            trace_data = generate_extreme_trace(trace_id, span_count)
            
            try:
                response = requests.post(
                    COLLECTOR_URL,
                    json=trace_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ 极端Trace{trace_num+1}: {span_count} spans")
                else:
                    print(f"  ❌ 极端Trace{trace_num+1}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 极端Trace{trace_num+1}: {e}")
        
        time.sleep(0.5)  # 批次间隔
    
    # 使用多线程快速发送
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        
        for batch_id in range(1, total_batches + 1):
            future = executor.submit(send_extreme_batch, batch_id)
            futures.append(future)
            time.sleep(0.1)  # 快速发送以填满buffer
        
        # 等待所有批次完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"批次处理错误: {e}")
    
    print("="*80)
    print("🎯 极端压力测试完成！")
    print(f"📊 已发送 {total_batches * batch_size} 个超复杂traces")
    print("🔬 应该已经触发高级遗传算法的RMSE、百分位数分析等功能")
    print("📝 检查collector日志查看详细的高级算法执行结果...")

if __name__ == "__main__":
    extreme_stress_test()
