#!/usr/bin/env python3
import requests
import json
import time
import random
import threading
import concurrent.futures

# OTLP HTTP endpoint for our custom collector
COLLECTOR_URL = "http://localhost:8326/v1/traces"

def generate_complex_trace(trace_id, span_count=8):
    """生成更复杂的测试trace数据来触发遗传算法"""
    spans = []
    base_time = int(time.time() * 1_000_000_000)  # nanoseconds
    
    # 生成更多样化的数据来触发更复杂的遗传算法逻辑
    service_types = ["auth", "payment", "inventory", "recommendation", "social-graph", "timeline"]
    error_rates = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2]  # 不同的错误率
    latencies = [
        (10_000_000, 50_000_000),    # 快速服务 10-50ms
        (50_000_000, 200_000_000),   # 中等服务 50-200ms  
        (200_000_000, 800_000_000),  # 慢速服务 200-800ms
        (800_000_000, 2_000_000_000) # 非常慢 0.8-2s
    ]
    
    for i in range(span_count):
        span_id = f"{i+1:016x}"
        service_type = random.choice(service_types)
        error_rate = random.choice(error_rates)
        latency_range = random.choice(latencies)
        duration = random.randint(latency_range[0], latency_range[1])
        
        # 更复杂的状态码分布
        if error_rate > 0.1:
            status_code = random.choice([0, 0, 1, 2])  # 高错误率
        else:
            status_code = random.choice([0, 0, 0, 0, 0, 0, 1])  # 低错误率
        
        span = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": f"{service_type}-operation-{i+1}",
            "kind": random.choice([1, 2, 3, 4]),  # 不同span类型
            "startTimeUnixNano": str(base_time + i * 1_000_000),
            "endTimeUnixNano": str(base_time + i * 1_000_000 + duration),
            "attributes": [
                {"key": "service.name", "value": {"stringValue": f"{service_type}-service"}},
                {"key": "latency.ms", "value": {"doubleValue": duration / 1_000_000}},
                {"key": "error.rate", "value": {"doubleValue": error_rate}},
                {"key": "throughput", "value": {"doubleValue": random.uniform(100, 10000)}},
                {"key": "cpu.usage", "value": {"doubleValue": random.uniform(0.1, 0.95)}},
                {"key": "memory.usage", "value": {"doubleValue": random.uniform(0.2, 0.8)}},
                {"key": "operation.complexity", "value": {"intValue": random.randint(1, 10)}}
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
                    {"key": "service.name", "value": {"stringValue": f"complex-microservice-{random.randint(1,5)}"}},
                    {"key": "service.version", "value": {"stringValue": "2.0.0"}},
                    {"key": "deployment.environment", "value": {"stringValue": random.choice(["prod", "staging", "dev"])}}
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "advanced-test-scope"},
                "spans": spans
            }]
        }]
    }

def send_trace_batch(batch_id, traces_per_batch=5):
    """发送一批traces"""
    print(f"批次 {batch_id}: 开始发送 {traces_per_batch} 个traces...")
    
    for trace_num in range(traces_per_batch):
        trace_id = f"{batch_id:04x}{trace_num+1:028x}"
        span_count = random.randint(5, 12)  # 更多spans以增加复杂性
        
        trace_data = generate_complex_trace(trace_id, span_count)
        
        try:
            response = requests.post(
                COLLECTOR_URL,
                json=trace_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"  ✅ 批次{batch_id}-Trace{trace_num+1}: {span_count} spans")
            else:
                print(f"  ❌ 批次{batch_id}-Trace{trace_num+1}: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 批次{batch_id}-Trace{trace_num+1}: {e}")
        
        time.sleep(0.1)  # 短间隔

def stress_test_genetic_algorithm():
    """压力测试遗传算法"""
    print("🧬 开始高级遗传算法压力测试...")
    print("目标：触发RMSE计算、百分位数分析、矩阵运算等高级功能")
    print("="*60)
    
    # 使用多线程发送大量traces
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        # 发送多批次，每批次5个traces，总共20批次 = 100个traces
        for batch_id in range(1, 21):
            future = executor.submit(send_trace_batch, batch_id, 5)
            futures.append(future)
            time.sleep(0.2)  # 批次间稍微间隔
        
        # 等待所有批次完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"批次处理错误: {e}")
    
    print("="*60)
    print("🎯 完成！应该已经触发遗传算法的高级功能")
    print("📊 检查collector日志查看RMSE、百分位数分析等结果...")

if __name__ == "__main__":
    stress_test_genetic_algorithm()
