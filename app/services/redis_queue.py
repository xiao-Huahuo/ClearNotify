import json
import redis
import logging
from typing import Optional
from app.core.config import GlobalConfig # 从全局配置导入

logger = logging.getLogger(__name__)

class RedisQueue:
    def __init__(self, host=GlobalConfig.REDIS_HOST, port=GlobalConfig.REDIS_PORT, 
                 db=GlobalConfig.REDIS_DB_QUEUE, name=GlobalConfig.REDIS_QUEUE_NAME):
        self.name = name
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis queue '{self.name}'.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis for queue '{self.name}': {e}. Queue will not function.")
            self.redis_client = None

    def enqueue(self, task_data: dict):
        """将任务数据推送到队列末尾"""
        if not self.redis_client:
            logger.error("Redis client not initialized. Cannot enqueue task.")
            return False
        try:
            self.redis_client.rpush(self.name, json.dumps(task_data))
            logger.info(f"Enqueued task: {task_data}")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_data}: {e}")
            return False

    def dequeue(self, timeout: int = 0) -> Optional[dict]:
        """从队列头部取出任务，如果队列为空则阻塞直到有任务或超时"""
        if not self.redis_client:
            logger.error("Redis client not initialized. Cannot dequeue task.")
            return None
        try:
            # blpop 返回一个元组 (list_name, item)
            item = self.redis_client.blpop(self.name, timeout=timeout)
            if item:
                task_data = json.loads(item[1])
                logger.info(f"Dequeued task: {task_data}")
                return task_data
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None

# 全局队列实例
crawler_queue = RedisQueue()
