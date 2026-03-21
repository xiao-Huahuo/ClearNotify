import logging
import time
from app.services.redis_queue import crawler_queue
from app.services import news_crawler # 导入所有爬虫函数

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局标志，用于控制 worker 的运行
_worker_running = False

def process_task(task: dict):
    task_type = task.get("type")
    logger.info(f"Processing task: {task_type} with args: {task.get('args')}")
    kwargs = task.get("kwargs", {})
    try:
        # 爬虫函数会自行将结果写入 Redis 缓存
        if task_type == "update_hot_news":
            news_crawler.get_hot_news(limit=kwargs.get("limit", 10))
            logger.info("Hot news updated in cache.")
        elif task_type == "update_central_docs":
            news_crawler.get_central_docs(limit=kwargs.get("limit", 5))
            logger.info("Central docs updated in cache.")
        elif task_type == "update_news_with_images":
            news_crawler.get_news_with_images(limit=kwargs.get("limit", 5))
            logger.info("News with images updated in cache.")
        elif task_type == "update_daily_gov_summary":
            news_crawler.get_daily_gov_summary()
            logger.info("Daily gov summary updated in cache.")
        elif task_type == "update_hot_keywords":
            news_crawler.get_hot_keywords()
            logger.info("Hot keywords updated in cache.")
        # 可以根据需要添加更多任务类型
        else:
            logger.warning(f"Unknown task type: {task_type}")
    except Exception as e:
        logger.error(f"Error processing task {task_type}: {e}")

def start_worker():
    global _worker_running
    _worker_running = True
    logger.info("Starting Redis queue worker...")
    while _worker_running:
        # 阻塞1秒等待任务，以便能及时响应停止信号
        task = crawler_queue.dequeue(timeout=1) 
        if task:
            process_task(task)
        else:
            logger.debug("No task in queue, waiting...")
        # 不需要额外的 time.sleep(1)，因为 dequeue 的 timeout 已经提供了等待
    logger.info("Redis queue worker stopped.")

def stop_worker():
    global _worker_running
    _worker_running = False
    logger.info("Stopping Redis queue worker...")

if __name__ == "__main__":
    # 如果直接运行 worker.py，则启动 worker
    start_worker()
