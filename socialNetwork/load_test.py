#!/usr/bin/env python3
"""
真实的DeathStarBench负载测试脚本
生成真实的API调用来触发微服务间的traces
"""

import requests
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SocialNetworkLoadTest:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.users = []
        self.user_tokens = {}
        
    def register_user(self, user_id):
        """注册用户"""
        try:
            data = {
                "username": f"user_{user_id}",
                "first_name": f"User{user_id}",
                "last_name": f"Test{user_id}",
                "password": f"password{user_id}"
            }
            
            response = self.session.post(f"{self.base_url}/wrk2-api/user/register", 
                                       json=data)
            if response.status_code == 200:
                logger.info(f"用户 user_{user_id} 注册成功")
                return True
            else:
                logger.warning(f"用户注册失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"注册用户时出错: {e}")
            return False
    
    def login_user(self, user_id):
        """用户登录"""
        try:
            data = {
                "username": f"user_{user_id}",
                "password": f"password{user_id}"
            }
            
            response = self.session.post(f"{self.base_url}/wrk2-api/user/login", 
                                       json=data)
            if response.status_code == 200:
                logger.info(f"用户 user_{user_id} 登录成功")
                return True
            else:
                logger.warning(f"用户登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"登录用户时出错: {e}")
            return False
    
    def compose_post(self, user_id):
        """发布帖子"""
        try:
            posts = [
                "刚刚完成了一个有趣的项目！#编程",
                "今天天气真不错，适合出去走走 🌞",
                "分享一下我最近读的好书",
                "和朋友们聚餐，开心！",
                "正在学习新技术，感觉很有挑战性",
                "周末计划去爬山，有人一起吗？",
                "刚看完一部很棒的电影，推荐给大家",
                "今天的工作效率特别高！"
            ]
            
            post_text = random.choice(posts)
            
            data = {
                "username": f"user_{user_id}",
                "post_type": 0,  # 普通帖子
                "text": post_text,
                "media_ids": [],
                "media_types": [],
                "post_id": -1  # 自动生成
            }
            
            response = self.session.post(f"{self.base_url}/wrk2-api/post/compose", 
                                       json=data)
            if response.status_code == 200:
                logger.info(f"用户 user_{user_id} 发布帖子成功: {post_text[:20]}...")
                return True
            else:
                logger.warning(f"发布帖子失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"发布帖子时出错: {e}")
            return False
    
    def read_home_timeline(self, user_id):
        """读取主页时间线"""
        try:
            params = {
                "user_id": user_id,
                "start": 0,
                "stop": 10
            }
            
            response = self.session.get(f"{self.base_url}/wrk2-api/home-timeline/read", 
                                      params=params)
            if response.status_code == 200:
                logger.info(f"用户 {user_id} 读取主页时间线成功")
                return True
            else:
                logger.warning(f"读取时间线失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"读取时间线时出错: {e}")
            return False
    
    def read_user_timeline(self, user_id):
        """读取用户时间线"""
        try:
            params = {
                "user_id": user_id,
                "start": 0,
                "stop": 10
            }
            
            response = self.session.get(f"{self.base_url}/wrk2-api/user-timeline/read", 
                                      params=params)
            if response.status_code == 200:
                logger.info(f"读取用户 {user_id} 时间线成功")
                return True
            else:
                logger.warning(f"读取用户时间线失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"读取用户时间线时出错: {e}")
            return False
    
    def follow_user(self, follower_id, followee_id):
        """关注用户"""
        try:
            data = {
                "user_id": follower_id,
                "followee_id": followee_id
            }
            
            response = self.session.post(f"{self.base_url}/wrk2-api/user/follow", 
                                       json=data)
            if response.status_code == 200:
                logger.info(f"用户 {follower_id} 关注用户 {followee_id} 成功")
                return True
            else:
                logger.warning(f"关注用户失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"关注用户时出错: {e}")
            return False
    
    def user_activity_thread(self, user_id, duration=30):
        """单个用户的活动线程"""
        logger.info(f"开始用户 {user_id} 的活动，持续 {duration} 秒")
        
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration:
            try:
                # 随机选择操作
                action = random.choice([
                    'compose_post',
                    'read_home_timeline', 
                    'read_user_timeline',
                    'follow_user'
                ])
                
                if action == 'compose_post':
                    self.compose_post(user_id)
                elif action == 'read_home_timeline':
                    self.read_home_timeline(user_id)
                elif action == 'read_user_timeline':
                    self.read_user_timeline(user_id)
                elif action == 'follow_user':
                    # 随机关注另一个用户
                    other_user = random.randint(1, min(50, len(self.users)))
                    if other_user != user_id:
                        self.follow_user(user_id, other_user)
                
                operations += 1
                
                # 随机等待时间，模拟真实用户行为
                time.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                logger.error(f"用户 {user_id} 活动出错: {e}")
                time.sleep(1)
        
        logger.info(f"用户 {user_id} 完成 {operations} 个操作")
    
    def run_load_test(self, num_users=10, duration=60):
        """运行负载测试"""
        logger.info(f"开始负载测试: {num_users} 个用户，持续 {duration} 秒")
        
        # 使用已有用户（从数据库初始化的用户）
        self.users = list(range(1, num_users + 1))
        
        # 启动用户活动线程
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            for user_id in self.users:
                future = executor.submit(self.user_activity_thread, user_id, duration)
                futures.append(future)
            
            # 等待所有线程完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"线程执行错误: {e}")
        
        logger.info("负载测试完成！")
        
        # 等待一下，让traces传输完成
        logger.info("等待5秒让traces传输完成...")
        time.sleep(5)

def main():
    load_tester = SocialNetworkLoadTest()
    
    logger.info("=" * 50)
    logger.info("DeathStarBench 社交网络负载测试")
    logger.info("=" * 50)
    
    # 运行负载测试
    # 使用50个用户（已经初始化过的），测试60秒
    load_tester.run_load_test(num_users=50, duration=60)
    
    logger.info("测试完成！请检查collector日志查看traces处理情况")

if __name__ == "__main__":
    main()
