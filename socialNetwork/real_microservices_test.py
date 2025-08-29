#!/usr/bin/env python3
"""
真实DeathStarBench社交网络微服务测试
使用真实API调用来触发traces，测试遗传算法collector
"""
import requests
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# 社交网络API基础URL
BASE_URL = "http://localhost:8080/wrk2-api"

class SocialNetworkTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_tokens = {}
        self.registered_users = []
        
    def register_user(self, username, password="password123", first_name="Test", last_name="User"):
        """注册新用户"""
        url = f"{BASE_URL}/user/register"
        data = {
            "username": username,
            "password": password,
            "first_name": first_name,
            "last_name": last_name
        }
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 用户注册成功: {username}")
                self.registered_users.append(username)
                return True
            else:
                print(f"❌ 用户注册失败: {username} - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 注册异常: {username} - {e}")
            return False
    
    def login_user(self, username, password="password123"):
        """用户登录"""
        url = f"{BASE_URL}/user/login"
        data = {
            "username": username,
            "password": password
        }
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 用户登录成功: {username}")
                return True
            else:
                print(f"❌ 用户登录失败: {username} - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {username} - {e}")
            return False
    
    def compose_post(self, user_id, username, text):
        """发布帖子"""
        url = f"{BASE_URL}/post/compose"
        data = {
            "username": username,
            "user_id": user_id,
            "text": text,
            "media_ids": "[]",
            "media_types": "[]",
            "post_type": 0
        }
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 帖子发布成功: {username} - '{text[:30]}...'")
                return True
            else:
                print(f"❌ 帖子发布失败: {username} - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 发布异常: {username} - {e}")
            return False
    
    def follow_user(self, user_id, username, followee_id, followee_name):
        """关注用户"""
        url = f"{BASE_URL}/user/follow"
        data = {
            "user_id": user_id,
            "username": username,
            "followee_id": followee_id,
            "followee_name": followee_name
        }
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 关注成功: {username} -> {followee_name}")
                return True
            else:
                print(f"❌ 关注失败: {username} -> {followee_name} - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 关注异常: {username} -> {followee_name} - {e}")
            return False
    
    def read_home_timeline(self, user_id, username, start=0, stop=10):
        """读取主页时间线"""
        url = f"{BASE_URL}/home-timeline/read"
        params = {
            "user_id": user_id,
            "start": start,
            "stop": stop
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                print(f"✅ 时间线读取成功: {username}")
                return True
            else:
                print(f"❌ 时间线读取失败: {username} - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 时间线异常: {username} - {e}")
            return False
    
    def read_user_timeline(self, user_id, username, start=0, stop=10):
        """读取用户时间线"""
        url = f"{BASE_URL}/user-timeline/read"
        params = {
            "user_id": user_id,
            "start": start,
            "stop": stop
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                print(f"✅ 用户时间线读取成功: {username}")
                return True
            else:
                print(f"❌ 用户时间线读取失败: {username} - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 用户时间线异常: {username} - {e}")
            return False

def simulate_user_behavior(tester, user_id, username):
    """模拟用户行为"""
    # 随机选择操作
    operations = [
        lambda: tester.compose_post(user_id, username, 
            f"这是来自{username}的帖子 #{random.randint(1, 1000)} - {random.choice(['工作', '生活', '学习', '娱乐', '旅行'])}相关内容"),
        lambda: tester.read_home_timeline(user_id, username, 0, random.randint(5, 20)),
        lambda: tester.read_user_timeline(user_id, username, 0, random.randint(3, 15)),
    ]
    
    # 随机执行1-3个操作
    num_operations = random.randint(1, 3)
    for _ in range(num_operations):
        operation = random.choice(operations)
        operation()
        time.sleep(random.uniform(0.5, 2.0))  # 模拟用户思考时间

def real_microservices_test():
    """真实微服务压力测试"""
    print("🌐 开始真实DeathStarBench社交网络微服务测试")
    print("🎯 目标：通过真实API调用生成traces，测试遗传算法collector")
    print("="*80)
    
    tester = SocialNetworkTester()
    
    # 1. 注册测试用户
    print("\n📝 步骤1: 注册测试用户...")
    usernames = [f"testuser{i}" for i in range(1, 21)]  # 20个测试用户
    
    for username in usernames:
        tester.register_user(username)
        time.sleep(0.2)  # 避免请求过快
    
    # 2. 用户登录
    print("\n🔐 步骤2: 用户登录...")
    active_users = []
    for i, username in enumerate(usernames[:15]):  # 选择15个用户作为活跃用户
        if tester.login_user(username):
            active_users.append((i+1, username))
        time.sleep(0.3)
    
    if not active_users:
        print("❌ 没有成功登录的用户，无法继续测试")
        return
    
    # 3. 建立社交关系
    print("\n👥 步骤3: 建立社交关系...")
    for i, (user_id, username) in enumerate(active_users):
        # 每个用户随机关注2-5个其他用户
        other_users = [u for u in active_users if u[1] != username]
        follow_count = min(random.randint(2, 5), len(other_users))
        follow_targets = random.sample(other_users, follow_count)
        
        for target_id, target_username in follow_targets:
            tester.follow_user(user_id, username, target_id, target_username)
            time.sleep(0.2)
    
    # 4. 模拟真实用户活动
    print("\n🎭 步骤4: 模拟真实用户活动...")
    print("这将生成大量真实的微服务traces...")
    
    # 使用多线程模拟并发用户
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        
        # 每个用户执行多轮操作
        for round_num in range(5):  # 5轮操作
            print(f"\n🔄 第{round_num+1}轮用户活动...")
            
            for user_id, username in active_users:
                future = executor.submit(simulate_user_behavior, tester, user_id, username)
                futures.append(future)
                time.sleep(0.1)  # 避免同时启动过多请求
            
            # 等待这一轮完成
            for future in futures[-len(active_users):]:
                try:
                    future.result(timeout=30)
                except Exception as e:
                    print(f"⚠️ 用户操作异常: {e}")
            
            time.sleep(2)  # 轮次间隔
    
    print("\n" + "="*80)
    print("🎯 真实微服务测试完成！")
    print("📊 统计:")
    print(f"  - 注册用户: {len(usernames)}")
    print(f"  - 活跃用户: {len(active_users)}")
    print(f"  - 操作轮次: 5")
    print(f"  - 预计API调用: {len(active_users) * 5 * 2}+ 次")
    print("🔬 检查collector日志查看遗传算法处理真实traces的结果...")

if __name__ == "__main__":
    real_microservices_test()
