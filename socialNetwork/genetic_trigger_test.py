#!/usr/bin/env python3
"""
专门为触发遗传算法设计的负载测试
"""

import time
import logging
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import requests

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeneticTriggerTest:
    def __init__(self):
        # 配置OpenTelemetry
        trace.set_tracer_provider(TracerProvider())
        tracer_provider = trace.get_tracer_provider()
        
        # 配置OTLP导出器
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:8325",
            insecure=True
        )
        
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        self.tracer = trace.get_tracer(__name__)
        self.base_url = "http://localhost:8080"
        
        # 操作类型配置 - 增加异常操作的比例
        self.operations = [
            ("read_user_timeline", 0.3),     # 30% 成功操作
            ("read_home_timeline", 0.2),     # 20% 成功操作  
            ("compose_post", 0.5),           # 50% 异常操作（会失败）
        ]
        
        self.users = list(range(1, 21))  # 20个用户
        
    def weighted_choice(self, choices):
        """根据权重选择操作"""
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        upto = 0
        for choice, weight in choices:
            if upto + weight >= r:
                return choice
            upto += weight
        return choices[-1][0]
    
    def execute_operation(self, user_id, operation):
        """执行单个操作"""
        with self.tracer.start_as_current_span(operation) as span:
            span.set_attribute("user.id", user_id)
            span.set_attribute("service.name", "genetic-trigger-test")
            span.set_attribute("operation.name", operation)
            
            start_time = time.time()
            
            try:
                if operation == "read_user_timeline":
                    url = f"{self.base_url}/wrk2-api/user-timeline/read"
                    params = {"user_id": user_id, "start": 0, "stop": 10}
                    response = requests.get(url, params=params, timeout=5)
                    
                elif operation == "read_home_timeline":
                    url = f"{self.base_url}/wrk2-api/home-timeline/read"
                    params = {"user_id": user_id, "start": 0, "stop": 10}
                    response = requests.get(url, params=params, timeout=5)
                    
                elif operation == "compose_post":
                    url = f"{self.base_url}/wrk2-api/post/compose"
                    data = {
                        "username": f"user_{user_id}",
                        "user_id": user_id,
                        "text": f"遗传算法测试帖子 #{random.randint(1000, 9999)}",
                        "media_ids": [],
                        "media_types": [],
                        "post_type": 0
                    }
                    response = requests.post(url, json=data, timeout=5)
                
                response_time = (time.time() - start_time) * 1000
                
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("response.time_ms", response_time)
                
                if response.status_code == 200:
                    span.set_attribute("operation.result", "success")
                    logger.info(f"用户 {user_id} {operation} 成功 (耗时: {response_time:.1f}ms)")
                else:
                    span.set_attribute("operation.result", "error")
                    span.set_attribute("error.message", f"HTTP {response.status_code}")
                    logger.warning(f"用户 {user_id} {operation} 失败: {response.status_code}")
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                span.set_attribute("operation.result", "error")
                span.set_attribute("error.message", str(e))
                span.set_attribute("response.time_ms", response_time)
                logger.error(f"用户 {user_id} {operation} 异常: {e}")
    
    def user_worker(self, user_id, duration):
        """单个用户的工作线程"""
        end_time = time.time() + duration
        operation_count = 0
        
        while time.time() < end_time:
            operation = self.weighted_choice(self.operations)
            self.execute_operation(user_id, operation)
            operation_count += 1
            
            # 随机延迟 0.5-2秒
            time.sleep(random.uniform(0.5, 2.0))
        
        logger.info(f"用户 {user_id} 完成 {operation_count} 个操作")
    
    def run_test(self, num_users=20, duration=120):
        """运行负载测试"""
        logger.info(f"🧬 开始遗传算法触发测试：{num_users} 用户，{duration} 秒")
        logger.info("配置说明：50%异常操作，确保触发遗传算法优化")
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            for user_id in self.users[:num_users]:
                future = executor.submit(self.user_worker, user_id, duration)
                futures.append(future)
            
            # 等待所有线程完成
            for future in futures:
                future.result()
        
        logger.info("🎯 遗传算法触发测试完成！")

if __name__ == "__main__":
    tester = GeneticTriggerTest()
    tester.run_test(num_users=20, duration=120)
