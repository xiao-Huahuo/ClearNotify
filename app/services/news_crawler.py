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

logger = logging.getLogger(__name__)

# ── 缓存 ──────────────────────────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 600  # 10 分钟

def _get_cache(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < CACHE_TTL:
        return entry["data"]
    return None

def _set_cache(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}

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

def _fetch_url(url: str, timeout: int = 5) -> Optional[str]:
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
        {"title": "习近平主持召开中央全面深化改革委员会第四次会议", "link": "https://www.gov.cn", "pubDate": "", "description": "会议审议通过了多项重要改革方案"},
        {"title": "国务院常务会议研究部署稳增长相关工作", "link": "https://www.gov.cn", "pubDate": "", "description": "会议强调要持续推动经济高质量发展"},
        {"title": "全国人大常委会审议多项重要法律草案", "link": "https://www.npc.gov.cn", "pubDate": "", "description": "涉及民生保障、数字经济等多个领域"},
        {"title": "中央经济工作会议精神贯彻落实情况综述", "link": "https://www.gov.cn", "pubDate": "", "description": "各地积极推进经济工作部署落地见效"},
        {"title": "国家发展改革委发布重大项目投资计划", "link": "https://www.ndrc.gov.cn", "pubDate": "", "description": "重点支持新基建、绿色发展等领域"},
        {"title": "财政部出台系列减税降费政策措施", "link": "https://www.mof.gov.cn", "pubDate": "", "description": "进一步减轻市场主体负担，激发市场活力"},
        {"title": "人力资源社会保障部发布就业形势分析报告", "link": "https://www.mohrss.gov.cn", "pubDate": "", "description": "就业形势总体稳定，重点群体就业保障有力"},
        {"title": "生态环境部通报全国空气质量改善情况", "link": "https://www.mee.gov.cn", "pubDate": "", "description": "主要城市空气质量持续改善"},
        {"title": "教育部部署推进教育强国建设重点工作", "link": "https://www.moe.gov.cn", "pubDate": "", "description": "聚焦提升教育质量和教育公平"},
        {"title": "卫生健康委发布最新医疗卫生服务数据", "link": "https://www.nhc.gov.cn", "pubDate": "", "description": "基层医疗服务能力持续提升"},
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
    return results[:limit]


# ── 带图片的热点资讯（用于主页图片横条）────────────────────────────────────────
def get_news_with_images(limit: int = 5) -> list[dict]:
    """返回带图片占位的热点资讯，图片从新闻源提取或使用占位"""
    cached = _get_cache("news_with_images")
    if cached:
        return cached[:limit]

    news = get_hot_news(10)
    # 为每条新闻附加一个图片占位,TODO:实际图片需要爬取，此处用占位色块数据
    colors = ["#c0392b", "#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#16a085", "#d35400", "#2c3e50"]
    result = []
    for i, item in enumerate(news[:limit]):
        result.append({
            **item,
            "image_color": colors[i % len(colors)],
            "image_url": None,  # 实际爬取图片时填充
            "category": "时事",
        })
    _set_cache("news_with_images", result)
    return result[:limit]


# ── 今日政务概况 ──────────────────────────────────────────────────────────────
def get_daily_gov_summary() -> dict:
    """返回今日政务概况数据"""
    cached = _get_cache("daily_summary")
    if cached:
        return cached

    news = get_hot_news(10)
    docs = get_central_docs(5)
    summary = {
        "news_count": len(news),
        "doc_count": len(docs),
        "top_news": news[0]["title"] if news else "暂无数据",
        "top_doc": docs[0]["title"] if docs else "暂无数据",
        "update_time": time.strftime("%H:%M", time.localtime()),
    }
    _set_cache("daily_summary", summary)
    return summary


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
