from fastapi import APIRouter, HTTPException, Query, Request

from app.services.news_crawler import (
    _get_cache,
    get_central_docs,
    get_daily_gov_summary,
    get_hot_keywords,
    get_hot_news,
    get_news_with_images,
    search_news,
)
from app.services.rate_limit_service import allow_request
from app.services.redis_queue import crawler_queue


router = APIRouter()


def _enforce_rate_limit(request: Request, bucket: str):
    client_ip = request.client.host if request.client else "unknown"
    if not allow_request(bucket=bucket, identifier=client_ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


async def _trigger_crawler_task(task_type: str, key: str, fallback_func, *args, **kwargs):
    cached_data = _get_cache(key)
    if cached_data:
        return cached_data

    task_data = {"type": task_type, "args": args, "kwargs": kwargs}
    crawler_queue.enqueue(task_data)
    return fallback_func(*args, **kwargs)


@router.get("/hot")
async def hot_news(request: Request, limit: int = 10):
    _enforce_rate_limit(request, "news_hot")
    items = await _trigger_crawler_task(
        "update_hot_news", "hot_news", get_hot_news, limit=limit
    )
    return {"items": items[:limit] if items else []}


@router.get("/central-docs")
async def central_docs(request: Request, limit: int = 5):
    _enforce_rate_limit(request, "news_docs")
    items = await _trigger_crawler_task(
        "update_central_docs", "central_docs", get_central_docs, limit=limit
    )
    return {"items": items[:limit] if items else []}


@router.get("/keywords")
async def hot_keywords(request: Request):
    _enforce_rate_limit(request, "news_keywords")
    items = await _trigger_crawler_task(
        "update_hot_keywords", "hot_keywords", get_hot_keywords
    )
    return {"items": items if items else []}


@router.get("/search")
async def news_search(
    request: Request,
    q: str = Query("", description="搜索关键词"),
    limit: int = 20,
):
    _enforce_rate_limit(request, "news_search")
    items = search_news(q, limit)
    return {"items": items, "query": q}


@router.get("/with-images")
async def news_with_images(request: Request, limit: int = 5):
    _enforce_rate_limit(request, "news_images")
    items = await _trigger_crawler_task(
        "update_news_with_images", "news_with_images", get_news_with_images, limit=limit
    )
    return {"items": items[:limit] if items else []}


@router.get("/daily-summary")
async def daily_summary(request: Request):
    _enforce_rate_limit(request, "news_summary")
    result = await _trigger_crawler_task(
        "update_daily_gov_summary", "daily_summary", get_daily_gov_summary
    )
    return result if result else {}
