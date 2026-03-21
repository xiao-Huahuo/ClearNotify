"""
新闻爬虫服务
- 时事热点：人民日报 RSS / 新华社 RSS
- 中央文件：中国政府网 RSS
带内存缓存，避免频繁请求
"""
import time
import logging
import xml.etree.ElementTree as ET
from typing import Optional
import urllib.request
import urllib.error
import json
import redis
import os
from app.core.config import GlobalConfig # 从全局配置导入

logger = logging.getLogger(__name__)
today = time.strftime("%Y-%m-%d")

# 初始化 Redis 客户端
# decode_responses=True 会自动将 Redis 返回的字节解码为字符串
redis_client = None
try:
    redis_client = redis.Redis(
        host=GlobalConfig.REDIS_HOST,
        port=GlobalConfig.REDIS_PORT,
        db=GlobalConfig.REDIS_DB_CACHE, # 使用缓存专用的DB
        decode_responses=True
    )
    redis_client.ping() # 尝试连接，如果失败会抛出异常
    logger.info("Successfully connected to Redis for caching.")
except redis.exceptions.ConnectionError as e:
    logger.error(f"Could not connect to Redis for caching: {e}. Falling back to in-memory cache.")
    redis_client = None # 如果连接失败，将 redis_client 设置为 None，以便后续使用内存缓存

# ── 缓存 ──────────────────────────────────────────────────────────────────────
_cache: dict = {} # 内存缓存，作为 Redis 不可用时的备用
CACHE_TTL = 600  # 10 分钟

def _get_cache(key: str):
    if redis_client:
        data = redis_client.get(key)
        if data:
            logger.debug(f"Redis cache hit for key: {key}")
            return json.loads(data) # 反序列化
        logger.debug(f"Redis cache miss for key: {key}")
        return None
    else: # Fallback to in-memory cache
        entry = _cache.get(key)
        if entry and time.time() - entry["ts"] < CACHE_TTL:
            logger.debug(f"In-memory cache hit for key: {key}")
            return entry["data"]
        logger.debug(f"In-memory cache miss for key: {key}")
        return None

def _set_cache(key: str, data):
    if redis_client:
        redis_client.setex(key, CACHE_TTL, json.dumps(data)) # 序列化
        logger.debug(f"Redis cache set for key: {key} with TTL: {CACHE_TTL}")
    else: # Fallback to in-memory cache
        _cache[key] = {"data": data, "ts": time.time()}
        logger.debug(f"In-memory cache set for key: {key}")

# ── HTTP 工具 ─────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def _fetch_url(url: str, timeout: int = 2) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            for enc in ("utf-8", "gbk", "utf-8-sig"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"fetch {url} failed: {e}")
        return None

# ── RSS 解析 ──────────────────────────────────────────────────────────────────
def _parse_rss(xml_text: str, limit: int = 20) -> list[dict]:
    """解析标准 RSS 2.0，返回 [{title, link, pubDate, description}]"""
    items = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        channel = root.find("channel")
        if channel is None:
            return items
        for item in channel.findall("item")[:limit]:
            def t(tag):
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else ""
            items.append({
                "title": t("title"),
                "link": t("link"),
                "pubDate": t("pubDate") or t("dc:date"),
                "description": t("description")[:200] if t("description") else "",
            })
    except ET.ParseError as e:
        logger.warning(f"RSS parse error: {e}")
    return items

# ── 时事热点 ──────────────────────────────────────────────────────────────────
# 多个 RSS 源，按优先级尝试
HOT_NEWS_SOURCES = [
    # 人民日报要闻
    "http://www.people.com.cn/rss/politics.xml",
    # 新华社国内
    "http://www.xinhuanet.com/politics/news_politics.xml",
    # 央视新闻
    "https://news.cctv.com/rss/china.xml",
]

def get_hot_news(limit: int = 10) -> list[dict]:
    cached = _get_cache("hot_news")
    if cached:
        return cached[:limit]

    all_items = []
    for url in HOT_NEWS_SOURCES:
        xml = _fetch_url(url)
        if xml:
            items = _parse_rss(xml, limit=20)
            if items:
                all_items.extend(items)
                if len(all_items) >= 20:
                    break

    # 去重（按标题）
    seen = set()
    unique = []
    for item in all_items:
        if item["title"] and item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    # 如果爬取失败，返回 mock 数据
    if not unique:
        unique = _mock_hot_news()

    _set_cache("hot_news", unique)
    return unique[:limit]

def _mock_hot_news() -> list[dict]:
    # TODO:加入真实爬虫逻辑获取真实热点数据
    return [
        {"title": "习近平主持召开中央全面深化改革委员会第四次会议", "link": "https://www.gov.cn", "pubDate": today,
         "description": "会议审议通过了多项重要改革方案"},
        {"title": "国务院常务会议研究部署稳增长相关工作", "link": "https://www.gov.cn", "pubDate": today,
         "description": "会议强调要持续推动经济高质量发展"},
        {"title": "全国人大常委会审议多项重要法律草案", "link": "https://www.npc.gov.cn", "pubDate": today,
         "description": "涉及民生保障、数字经济等多个领域"},
        {"title": "中央经济工作会议精神贯彻落实情况综述", "link": "https://www.gov.cn", "pubDate": today,
         "description": "各地积极推进经济工作部署落地见效"},
        {"title": "国家发展改革委发布重大项目投资计划", "link": "https://www.ndrc.gov.cn", "pubDate": today,
         "description": "重点支持新基建、绿色发展等领域"},
        {"title": "财政部出台系列减税降费政策措施", "link": "https://www.mof.gov.cn", "pubDate": today,
         "description": "进一步减轻市场主体负担，激发市场活力"},
        {"title": "人力资源社会保障部发布就业形势分析报告", "link": "https://www.mohrss.gov.cn", "pubDate": today,
         "description": "就业形势总体稳定，重点群体就业保障有力"},
        {"title": "生态环境部通报全国空气质量改善情况", "link": "https://www.mee.gov.cn", "pubDate": today,
         "description": "主要城市空气质量持续改善"},
        {"title": "教育部部署推进教育强国建设重点工作", "link": "https://www.moe.gov.cn", "pubDate": today,
         "description": "聚焦提升教育质量和教育公平"},
        {"title": "卫生健康委发布最新医疗卫生服务数据", "link": "https://www.nhc.gov.cn", "pubDate": today,
         "description": "基层医疗服务能力持续提升"},
    ]

# ── 中央文件 ──────────────────────────────────────────────────────────────────
CENTRAL_DOC_SOURCES = [
    # 国务院政策文件（备用源）
    "https://www.gov.cn/xinwen/rss/index.htm",
    "http://www.gov.cn/xinwen/rss/index.htm",
]

def get_central_docs(limit: int = 10) -> list[dict]:
    cached = _get_cache("central_docs")
    if cached:
        return cached[:limit]

    all_items = []
    for url in CENTRAL_DOC_SOURCES:
        xml = _fetch_url(url)
        if xml:
            items = _parse_rss(xml, limit=20)
            if items:
                all_items.extend(items)
                break

    if not all_items:
        all_items = _mock_central_docs()

    _set_cache("central_docs", all_items)
    return all_items[:limit]

def _mock_central_docs() -> list[dict]:
    # TODO:加入真实爬虫逻辑获取真实中央新闻数据
    return [
        {
            "title": "国务院关于进一步优化营商环境降低市场主体制度性交易成本的意见",
            "link": "https://www.gov.cn/zhengce/content/2024-01/01/content_1.htm",
            "pubDate": "2024-01-15",
            "description": '为深入贯彻党中央、国务院关于优化营商环境的决策部署，进一步降低市场主体制度性交易成本，激发市场活力和社会创造力，现提出以下意见。一、总体要求（一）指导思想。以习近平新时代中国特色社会主义思想为指导，全面贯彻党的二十大精神，坚持稳中求进工作总基调，完整、准确、全面贯彻新发展理念，加快构建新发展格局，着力推动高质量发展，持续深化"放管服"改革，不断优化营商环境，切实降低市场主体制度性交易成本，为经济社会高质量发展提供有力支撑。',
        },
        {
            "title": "中共中央 国务院关于做好2024年全面推进乡村振兴重点工作的意见",
            "link": "https://www.gov.cn/zhengce/content/2024-02/03/content_2.htm",
            "pubDate": "2024-02-03",
            "description": '这是21世纪以来第21个指导"三农"工作的中央一号文件。文件强调，要学习运用"千万工程"经验，有力有效推进乡村全面振兴，以加快农业农村现代化更好推进中国式现代化建设。',
        },
        {
            "title": "国务院办公厅关于加快发展新质生产力的若干政策措施",
            "link": "https://www.gov.cn/zhengce/content/2024-03/01/content_3.htm",
            "pubDate": "2024-03-01",
            "description": "为贯彻落实党中央关于发展新质生产力的重大决策部署，加快推动科技创新和产业创新深度融合，培育壮大新兴产业，超前布局建设未来产业，现提出以下政策措施。",
        },
        {
            "title": "关于深化医药卫生体制改革的若干意见",
            "link": "https://www.gov.cn/zhengce/content/2024-04/01/content_4.htm",
            "pubDate": "2024-04-01",
            "description": "深化医药卫生体制改革，是党中央、国务院作出的重大战略决策。要坚持以人民健康为中心，推动医疗、医保、医药协同发展和治理，促进优质医疗资源扩容下沉和区域均衡布局。",
        },
        {
            "title": "国务院关于推动内贸流通高质量发展的若干意见",
            "link": "https://www.gov.cn/zhengce/content/2024-05/01/content_5.htm",
            "pubDate": "2024-05-01",
            "description": "内贸流通是国民经济的重要组成部分，是连接生产和消费的重要纽带。为推动内贸流通高质量发展，更好服务构建新发展格局，现提出以下意见。",
        },
    ]

# ── 新闻搜索 ──────────────────────────────────────────────────────────────────
def search_news(query: str, limit: int = 20) -> list[dict]:
    """在热点新闻和中央文件中搜索关键词"""
    if not query.strip():
        return []
    news = get_hot_news(20)
    docs = get_central_docs(10)
    all_items = []
    for item in news:
        item["source_type"] = "news"
        all_items.append(item)
    for item in docs:
        item["source_type"] = "policy"
        all_items.append(item)
    q = query.lower()
    results = [
        item for item in all_items
        if q in (item.get("title") or "").lower()
        or q in (item.get("description") or "").lower()
    ]

    # 兜底：如果搜不到结果，提供静态 mock 数据
    if not results:
        return _mock_search_news(query)[:limit]

    return results[:limit]

def _mock_search_news(query: str) -> list[dict]:
    """搜索结果的 Mock 兜底"""
    return [
        {
            "title": f"关于“{query}”的最新政策解读",
            "link": "https://www.gov.cn",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": f"有关{query}的全面深化改革举措和政策说明，详细解释了下一步的发展方向。",
            "source_type": "policy"
        },
        {
            "title": f"【热点关注】{query} 成为近期社会重点议题",
            "link": "https://news.cctv.com",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": f"社会各界对{query}展开热烈讨论，专家指出其对未来经济民生将产生深远影响。",
            "source_type": "news"
        }
    ]

# ── 带图片的热点资讯（用于主页图片横条）────────────────────────────────────────
def get_news_with_images(limit: int = 5) -> list[dict]:
    """返回带图片占位的热点资讯，图片从新闻源提取或使用占位"""
    cached = _get_cache("news_with_images")
    if cached:
        return cached[:limit]

    news = get_hot_news(10)

    # 兜底：如果热点新闻提取失败或为空，直接使用预设的带图 mock 数据
    if not news:
        result = _mock_news_with_images()
        _set_cache("news_with_images", result)
        return result[:limit]

    # 为每条新闻附加一个图片占位,TODO:实际图片需要爬取，此处用占位色块数据
    colors = ["#c0392b", "#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#16a085", "#d35400", "#2c3e50"]
    # 提供一组备用占位图
    placeholders = [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=400&q=80"
    ]
    result = []
    for i, item in enumerate(news[:limit]):
        result.append({
            **item,
            "image_color": colors[i % len(colors)],
            "image_url": placeholders[i % len(placeholders)],  # 替换成占位图，不再返回 None
            "category": "时事",
        })
    _set_cache("news_with_images", result)
    return result[:limit]

def _mock_news_with_images() -> list[dict]:
    """带图资讯的 Mock 兜底"""
    return [
        {
            "title": "全国科技创新大会在京隆重召开",
            "link": "https://news.cctv.com",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": "会议强调加快实现高水平科技自立自强，为经济高质量发展提供坚实支撑。",
            "image_color": "#c0392b",
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80",
            "category": "时事"
        },
        {
            "title": "新能源汽车产销量创历史新高",
            "link": "https://news.cctv.com",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": "我国新能源汽车产业保持高速增长态势，绿色出行理念深入人心。",
            "image_color": "#2980b9",
            "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=400&q=80",
            "category": "经济"
        },
        {
            "title": "生态环境保护取得阶段性显著成果",
            "link": "https://news.cctv.com",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": "多地空气质量优良天数比例稳步提升，蓝天白云成为常态。",
            "image_color": "#27ae60",
            "image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80",
            "category": "生态"
        },
        {
            "title": "民生工程稳步推进，群众幸福感增强",
            "link": "https://news.cctv.com",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": "老旧小区改造、养老服务设施建设全面提速，打通服务群众的最后一公里。",
            "image_color": "#e67e22",
            "image_url": "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?auto=format&fit=crop&w=400&q=80",
            "category": "民生"
        },
        {
            "title": "文化产业高质量发展，数字化转型加速",
            "link": "https://news.cctv.com",
            "pubDate": time.strftime("%Y-%m-%d"),
            "description": "数字文化新业态成为激发消费新引擎，传统文化焕发新活力。",
            "image_color": "#8e44ad",
            "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=400&q=80",
            "category": "文化"
        }
    ]

# ── 今日政务概况 ──────────────────────────────────────────────────────────────
def get_daily_gov_summary() -> dict:
    """返回今日政务概况数据"""
    cached = _get_cache("daily_summary")
    if cached:
        return cached

    news = get_hot_news(10)
    docs = get_central_docs(5)

    # 兜底：如果没有任何新闻和政策文件，返回预设的 mock 数据
    if not news and not docs:
        summary = _mock_daily_gov_summary()
    else:
        summary = {
            "news_count": len(news) if news else 25,
            "doc_count": len(docs) if docs else 12,
            "top_news": news[0]["title"] if news else "全国科技创新大会在京隆重召开",
            "top_doc": docs[0]["title"] if docs else "关于进一步优化营商环境降低市场主体制度性交易成本的意见",
            "update_time": time.strftime("%H:%M", time.localtime()),
        }

    _set_cache("daily_summary", summary)
    return summary

def _mock_daily_gov_summary() -> dict:
    """政务概况的 Mock 兜底"""
    return {
        "news_count": 36,
        "doc_count": 15,
        "top_news": "模拟新闻：多措并举促进经济持续回升向好",
        "top_doc": "模拟文件：关于扎实推进城市更新工作的指导意见",
        "update_time": time.strftime("%H:%M", time.localtime()),
    }

# ── 热点关键词（用于点云图）────────────────────────────────────────────────────
def get_hot_keywords() -> list[dict]:
    """从热点新闻和中央文件中提取关键词，返回 [{name, value}] 用于 ECharts"""
    cached = _get_cache("hot_keywords")
    if cached:
        return cached

    # 合并所有标题
    news = get_hot_news(10)
    docs = get_central_docs(5)
    all_titles = [n["title"] for n in news] + [d["title"] for d in docs]

    # 兜底：如果完全没有获取到标题，返回静态的 mock 关键词
    if not all_titles:
        result = _mock_hot_keywords()
        _set_cache("hot_keywords", result)
        return result

    # 简单词频统计（不依赖 jieba，避免额外依赖）
    import re
    word_freq: dict[str, int] = {}
    # 政务常用词汇权重
    keywords_base = [
        ("改革", 95), ("发展", 90), ("政策", 85), ("经济", 88), ("民生", 80),
        ("创新", 82), ("数字化", 75), ("乡村振兴", 78), ("高质量", 85), ("新质生产力", 72),
        ("营商环境", 70), ("医疗", 68), ("教育", 72), ("就业", 75), ("生态", 65),
        ("安全", 80), ("法治", 70), ("党建", 65), ("科技", 78), ("绿色", 68),
        ("共同富裕", 72), ("数字经济", 75), ("人工智能", 70), ("碳中和", 65), ("乡村", 68),
    ]
    for kw, base_val in keywords_base:
        count = sum(1 for t in all_titles if kw in t)
        word_freq[kw] = base_val + count * 5

    result = [{"name": k, "value": v} for k, v in sorted(word_freq.items(), key=lambda x: -x[1])]
    _set_cache("hot_keywords", result)
    return result

def _mock_hot_keywords() -> list[dict]:
    """热点关键词的 Mock 兜底"""
    return [
        {"name": "高质量发展", "value": 150},
        {"name": "改革", "value": 135},
        {"name": "数字经济", "value": 120},
        {"name": "乡村振兴", "value": 115},
        {"name": "科技创新", "value": 110},
        {"name": "民生保障", "value": 105},
        {"name": "新质生产力", "value": 100},
        {"name": "营商环境", "value": 95},
        {"name": "绿色生态", "value": 90},
        {"name": "共同富裕", "value": 85}
    ]
