#!/usr/bin/env python3
"""
使用OpenTelemetry Python SDK直接向我们的collector发送traces的负载测试脚本
"""

import requests
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeathStarBenchTraceTest:
    def __init__(self, base_url="http://127.0.0.1:8080", collector_endpoint="http://127.0.0.1:8325"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # 配置OpenTelemetry追踪
        resource = Resource.create({"service.name": "deathstarbench-load-test"})
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # 配置OTLP exporter到我们的collector
        otlp_exporter = OTLPSpanExporter(
            endpoint=collector_endpoint,
            insecure=True
        )
        
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        self.tracer = trace.get_tracer(__name__)
        
    def read_home_timeline_with_trace(self, user_id):
        """读取主页时间线并生成trace"""
        with self.tracer.start_as_current_span("read_home_timeline") as span:
            span.set_attribute("user.id", user_id)
            span.set_attribute("service.name", "home-timeline-service")
            span.set_attribute("operation.name", "read_home_timeline")
            
            try:
                start_time = time.time()
                params = {
                    "user_id": user_id,
                    "start": 0,
                    "stop": 10
                }
                
                response = self.session.get(f"{self.base_url}/wrk2-api/home-timeline/read", 
                                          params=params)
                
                duration = time.time() - start_time
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("response.time_ms", duration * 1000)
                
                if response.status_code == 200:
                    span.set_attribute("operation.result", "success")
                    logger.info(f"用户 {user_id} 读取主页时间线成功 (耗时: {duration:.3f}s)")
                    return True
                else:
                    span.set_attribute("operation.result", "error")
                    span.set_attribute("error.message", response.text)
                    logger.warning(f"读取时间线失败: {response.status_code}")
                    return False
                    
            except Exception as e:
                span.set_attribute("operation.result", "exception")
                span.set_attribute("error.message", str(e))
                logger.error(f"读取时间线时出错: {e}")
                return False
    
    def read_user_timeline_with_trace(self, user_id):
        """读取用户时间线并生成trace"""
        with self.tracer.start_as_current_span("read_user_timeline") as span:
            span.set_attribute("user.id", user_id)
            span.set_attribute("service.name", "user-timeline-service")
            span.set_attribute("operation.name", "read_user_timeline")
            
            try:
                start_time = time.time()
                params = {
                    "user_id": user_id,
                    "start": 0,
                    "stop": 10
                }
                
                response = self.session.get(f"{self.base_url}/wrk2-api/user-timeline/read", 
                                          params=params)
                
                duration = time.time() - start_time
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("response.time_ms", duration * 1000)
                
                if response.status_code == 200:
                    span.set_attribute("operation.result", "success")
                    logger.info(f"读取用户 {user_id} 时间线成功 (耗时: {duration:.3f}s)")
                    return True
                else:
                    span.set_attribute("operation.result", "error")
                    span.set_attribute("error.message", response.text)
                    logger.warning(f"读取用户时间线失败: {response.status_code}")
                    return False
                    
            except Exception as e:
                span.set_attribute("operation.result", "exception")
                span.set_attribute("error.message", str(e))
                logger.error(f"读取用户时间线时出错: {e}")
                return False
    
    def compose_post_with_trace(self, user_id):
        """发布帖子并生成trace"""
        with self.tracer.start_as_current_span("compose_post") as span:
            span.set_attribute("user.id", user_id)
            span.set_attribute("service.name", "compose-post-service")
            span.set_attribute("operation.name", "compose_post")
            
            try:
                posts = [
                    "测试帖子：今天天气很好！",
                    "正在使用DeathStarBench进行压力测试",
                    "OpenTelemetry遗传算法collector测试中",
                    "分布式追踪系统性能优化实验",
                    "微服务架构下的trace采样优化"
                ]
                
                post_text = random.choice(posts)
                span.set_attribute("post.text", post_text[:50] + "...")
                
                start_time = time.time()
                data = {
                    "username": f"user_{user_id}",
                    "post_type": 0,
                    "text": post_text,
                    "media_ids": [],
                    "media_types": [],
                    "post_id": -1
                }
                
                response = self.session.post(f"{self.base_url}/wrk2-api/post/compose", 
                                           json=data)
                
                duration = time.time() - start_time
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("response.time_ms", duration * 1000)
                
                if response.status_code == 200:
                    span.set_attribute("operation.result", "success")
                    logger.info(f"用户 user_{user_id} 发布帖子成功 (耗时: {duration:.3f}s)")
                    return True
                else:
                    span.set_attribute("operation.result", "error")
                    span.set_attribute("error.message", response.text)
                    logger.warning(f"发布帖子失败: {response.status_code}")
                    return False
                    
            except Exception as e:
                span.set_attribute("operation.result", "exception")
                span.set_attribute("error.message", str(e))
                logger.error(f"发布帖子时出错: {e}")
                return False
    
    def user_activity_thread_with_traces(self, user_id, duration=30):
        """单个用户的活动线程，生成完整的traces"""
        logger.info(f"开始用户 {user_id} 的追踪活动，持续 {duration} 秒")
        
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration:
            try:
                # 随机选择操作
                action = random.choice([
                    'read_home_timeline',
                    'read_user_timeline', 
                    'compose_post'
                ])
                
                if action == 'read_home_timeline':
                    self.read_home_timeline_with_trace(user_id)
                elif action == 'read_user_timeline':
                    self.read_user_timeline_with_trace(user_id)
                elif action == 'compose_post':
                    self.compose_post_with_trace(user_id)
                
                operations += 1
                
                # 随机等待时间，模拟真实用户行为
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.error(f"用户 {user_id} 活动出错: {e}")
                time.sleep(1)
        
        logger.info(f"用户 {user_id} 完成 {operations} 个追踪操作")
    
    def run_traced_load_test(self, num_users=10, duration=60):
        """运行带traces的负载测试"""
        logger.info(f"开始OpenTelemetry追踪负载测试: {num_users} 个用户，持续 {duration} 秒")
        logger.info("Traces将直接发送到我们的collector")
        
        users = list(range(1, num_users + 1))
        
        # 启动用户活动线程
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            for user_id in users:
                future = executor.submit(self.user_activity_thread_with_traces, user_id, duration)
                futures.append(future)
            
            # 等待所有线程完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"线程执行错误: {e}")
        
        logger.info("OpenTelemetry追踪负载测试完成！")
        
        # 强制刷新所有pending spans
        for processor in trace.get_tracer_provider()._span_processors:
            processor.force_flush()
        
        logger.info("等待5秒让所有traces传输完成...")
        time.sleep(5)

def main():
    # 首先安装必要的包
    try:
        import opentelemetry
    except ImportError:
        print("正在安装OpenTelemetry包...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                             "opentelemetry-api", 
                             "opentelemetry-sdk", 
                             "opentelemetry-exporter-otlp-proto-grpc"])
        print("安装完成！")
    
    tester = DeathStarBenchTraceTest()
    
    logger.info("=" * 60)
    logger.info("DeathStarBench + OpenTelemetry 遗传算法Collector测试")
    logger.info("=" * 60)
    
    # 运行追踪负载测试
    tester.run_traced_load_test(num_users=20, duration=90)
    
    logger.info("测试完成！请检查collector日志查看遗传算法执行情况")

if __name__ == "__main__":
    main()
