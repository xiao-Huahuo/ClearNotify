from __future__ import annotations

import re
from typing import Any


ROLE_LABELS = {
    "normal": "普通用户",
    "certified": "认证主体",
    "admin": "管理员",
}

ROLE_KEYWORDS: dict[str, set[str]] = {
    "normal": {
        "个人", "居民", "市民", "家庭", "申请", "办理", "服务", "补贴", "资格", "流程",
    },
    "certified": {
        "企业", "公司", "单位", "机构", "主体", "申报", "备案", "资质", "经营", "项目",
    },
    "admin": {
        "部门", "监管", "审核", "治理", "执法", "规范", "统计", "核查", "监督", "行政",
    },
}

PROFESSION_EXPANSIONS: dict[str, set[str]] = {
    "企业": {"企业", "公司", "经营", "申报", "项目", "补贴", "备案", "资质", "融资", "园区"},
    "创业": {"创业", "初创", "孵化", "融资", "补贴", "项目", "创新", "企业"},
    "个体": {"个体工商户", "营业执照", "经营", "备案", "登记", "税费"},
    "财务": {"税务", "财政", "资金", "补贴", "发票", "审计", "经费"},
    "会计": {"税务", "财政", "资金", "补贴", "发票", "审计", "经费"},
    "人力": {"就业", "劳动", "社保", "招聘", "人才", "补贴", "用工"},
    "hr": {"就业", "劳动", "社保", "招聘", "人才", "补贴", "用工"},
    "法务": {"合规", "处罚", "条例", "监管", "法律", "责任", "审查"},
    "律师": {"合规", "处罚", "条例", "监管", "法律", "责任", "审查"},
    "教师": {"教育", "学校", "教师", "教职工", "课题", "科研", "培训"},
    "学生": {"学生", "高校", "校园", "毕业", "奖学金", "助学", "就业"},
    "科研": {"科研", "课题", "实验室", "成果", "项目", "经费"},
    "医生": {"医疗", "医院", "医保", "卫健", "医师", "门诊", "药品"},
    "护士": {"医疗", "医院", "医保", "卫健", "护理", "门诊"},
    "农业": {"农业", "农户", "种植", "养殖", "乡村", "农村", "农机"},
    "农": {"农业", "农户", "种植", "养殖", "乡村", "农村", "农机"},
    "公务员": {"政务", "政府", "行政", "机关", "监管", "审批", "治理"},
    "街道": {"社区", "基层", "街道", "治理", "服务", "民政"},
    "社区": {"社区", "基层", "街道", "治理", "服务", "民政"},
    "医生": {"医疗", "医院", "医保", "卫健", "医师", "门诊", "药品"},
    "工程": {"工程", "建设", "施工", "招投标", "项目", "规范"},
    "开发": {"技术", "软件", "数据", "开发", "系统", "平台"},
}

ACTION_KEYWORDS = {
    "申请", "申报", "办理", "提交", "审核", "认定", "备案", "登记", "领取", "兑付", "审批",
    "受理", "核验", "开通", "填报", "注册", "匹配", "享受",
}
MATERIAL_KEYWORDS = {
    "材料", "证明", "附件", "清单", "表格", "执照", "身份证", "户口", "发票", "合同",
    "申请书", "证书", "原件", "复印件",
}
ENTRANCE_KEYWORDS = {
    "窗口", "线上", "线下", "平台", "系统", "入口", "大厅", "部门", "网站", "小程序",
}
TIME_KEYWORDS = {
    "截止", "截至", "期限", "时限", "时间", "日期", "工作日", "有效期", "尽快", "年度",
}
RISK_KEYWORDS = {
    "风险", "处罚", "逾期", "不予", "禁止", "责任", "失信", "退回", "驳回", "约束",
}

TOKEN_SPLIT_RE = re.compile(r"[\s,，、/;；|]+")
MEANINGFUL_TERM_RE = re.compile(r"[\u4e00-\u9fff]{2,12}|[A-Za-z][A-Za-z0-9_+-]{2,24}")


def _flatten_text(value: Any, output: list[str], depth: int = 0) -> None:
    if depth > 6 or value is None:
        return
    if isinstance(value, str):
        text = value.strip()
        if text:
            output.append(text)
        return
    if isinstance(value, (int, float, bool)):
        output.append(str(value))
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str) and key.strip():
                output.append(key.strip())
            _flatten_text(nested, output, depth + 1)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            _flatten_text(item, output, depth + 1)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def _extract_meaningful_terms(value: str) -> list[str]:
    if not value:
        return []
    found = []
    seen = set()
    raw_parts = TOKEN_SPLIT_RE.split(str(value))
    for part in raw_parts:
        token = part.strip()
        if len(token) >= 2 and token not in seen:
            found.append(token)
            seen.add(token)
    for token in MEANINGFUL_TERM_RE.findall(str(value)):
        if len(token) >= 2 and token not in seen:
            found.append(token)
            seen.add(token)
    return found


def _build_profile_keywords(role: str | None, profession: str | None) -> tuple[set[str], set[str]]:
    role_raw = getattr(role, "value", role)
    role_key = str(role_raw or "normal").strip().lower() or "normal"
    role_keywords = set(ROLE_KEYWORDS.get(role_key, ROLE_KEYWORDS["normal"]))
    profession_keywords: set[str] = set()
    profession_text = str(profession or "").strip()
    for term in _extract_meaningful_terms(profession_text):
        profession_keywords.add(term)
        lowered = term.lower()
        for trigger, expansion in PROFESSION_EXPANSIONS.items():
            if trigger.lower() in lowered or lowered in trigger.lower():
                profession_keywords.update(expansion)
    return role_keywords, profession_keywords


def _keyword_hits(text: str, keywords: set[str]) -> list[str]:
    hits = []
    seen = set()
    for keyword in sorted(keywords, key=lambda item: (-len(item), item)):
        normalized = _normalize_text(keyword)
        if len(normalized) < 2:
            continue
        if normalized in text and normalized not in seen:
            hits.append(keyword)
            seen.add(normalized)
    return hits


def _coverage(hit_count: int, total_count: int, cap: int = 6) -> float:
    if total_count <= 0:
        return 0.0
    return min(hit_count / max(1, min(total_count, cap)), 1.0)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def build_personal_recommendation(
    *,
    role: str | None,
    profession: str | None,
    content: str,
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    dynamic_payload: dict[str, Any],
) -> dict[str, Any]:
    raw_text_parts: list[str] = [content or ""]
    _flatten_text(dynamic_payload, raw_text_parts)
    for node in nodes:
        if isinstance(node, dict):
            raw_text_parts.append(str(node.get("label") or ""))
            raw_text_parts.append(str(node.get("type") or ""))
            _flatten_text(node.get("properties"), raw_text_parts)
    for link in links:
        if isinstance(link, dict):
            raw_text_parts.append(str(link.get("relation") or ""))
            raw_text_parts.append(str(link.get("logic_type") or ""))
            raw_text_parts.append(str(link.get("evidence") or ""))

    document_text = _normalize_text(" ".join(part for part in raw_text_parts if part))
    role_raw = getattr(role, "value", role)
    role_value = str(role_raw or "normal").strip().lower() or "normal"
    role_label = ROLE_LABELS.get(role_value, "普通用户")
    role_keywords, profession_keywords = _build_profile_keywords(role_value, profession)

    profession_phrase = str(profession or "").strip()
    profession_phrase_hit = 1.0 if profession_phrase and _normalize_text(profession_phrase) in document_text else 0.0
    profession_hits = _keyword_hits(document_text, profession_keywords)
    role_hits = _keyword_hits(document_text, role_keywords)
    action_hits = _keyword_hits(document_text, ACTION_KEYWORDS)
    material_hits = _keyword_hits(document_text, MATERIAL_KEYWORDS)
    entrance_hits = _keyword_hits(document_text, ENTRANCE_KEYWORDS)
    time_hits = _keyword_hits(document_text, TIME_KEYWORDS)
    risk_hits = _keyword_hits(document_text, RISK_KEYWORDS)

    profession_score = 0.0
    if profession_keywords:
        profession_score = _clamp(
            0.45 * profession_phrase_hit
            + 0.55 * _coverage(len(profession_hits), len(profession_keywords)),
        )

    role_score = _clamp(_coverage(len(role_hits), len(role_keywords), cap=5))
    actionability_score = _clamp(
        0.42 * (1.0 if action_hits else 0.0)
        + 0.26 * (1.0 if material_hits else 0.0)
        + 0.18 * (1.0 if entrance_hits else 0.0)
        + 0.14 * min((len(action_hits) + len(material_hits)) / 4, 1.0)
    )
    urgency_score = _clamp(
        0.58 * (1.0 if time_hits else 0.0)
        + 0.42 * (1.0 if risk_hits else 0.0)
    )

    node_count = len(nodes)
    link_count = len(links)
    negative_edges = sum(1 for item in links if str(item.get("logic_type") or "") == "negative")
    complexity_score = _clamp(
        0.42 * (1.0 if node_count >= 10 or link_count >= 12 else 0.58 if node_count >= 6 or link_count >= 7 else 0.24)
        + 0.34 * (1.0 if len(content or "") >= 1200 else 0.56 if len(content or "") >= 500 else 0.22)
        + 0.24 * (1.0 if negative_edges >= 3 else 0.5 if negative_edges >= 1 else 0.12)
    )

    weighted_scores = {
        "profession": (profession_score, 0.30 if profession_keywords else 0.0),
        "role": (role_score, 0.22),
        "actionability": (actionability_score, 0.24),
        "urgency": (urgency_score, 0.14),
        "complexity": (complexity_score, 0.10),
    }
    total_weight = sum(weight for _, weight in weighted_scores.values()) or 1.0
    final_score = round(
        100
        * sum(score * weight for score, weight in weighted_scores.values())
        / total_weight
    )

    if final_score >= 80:
        level = "high"
        level_label = "高价值"
        priority_label = "建议优先办理"
    elif final_score >= 60:
        level = "medium"
        level_label = "值得重点阅读"
        priority_label = "建议重点阅读"
    elif final_score >= 40:
        level = "medium_low"
        level_label = "可收藏备查"
        priority_label = "建议收藏备查"
    else:
        level = "low"
        level_label = "按需浏览"
        priority_label = "按需浏览"

    profile_label = f"{role_label} / {profession_phrase}" if profession_phrase else role_label
    matched_keywords = list(dict.fromkeys(
        profession_hits[:4] + role_hits[:3] + action_hits[:2] + time_hits[:1] + material_hits[:1]
    ))[:6]

    reasons: list[str] = []
    if profession_hits or profession_phrase_hit:
        reasons.append(
            f"文档中出现了与您的职业画像相关的关键词：{'、'.join((profession_hits or [profession_phrase])[:4])}。"
        )
    elif role_hits:
        reasons.append(
            f"文档语义与您的角色侧重点接近，命中了 {'、'.join(role_hits[:3])} 等信号。"
        )
    if action_hits or material_hits or entrance_hits:
        reasons.append("文档包含明确的办理/申报/材料/入口信号，具备较强的可执行价值。")
    if time_hits or risk_hits:
        reasons.append("文档同时带有时间节点或约束风险提示，适合尽早关注。")
    if complexity_score >= 0.62:
        reasons.append("原文结构偏复杂，当前知识图谱与结构化结果能明显降低理解成本。")
    if not reasons:
        reasons.append("当前文档与您的直接画像匹配度一般，但仍可作为相关背景资料备用。")

    suggestions: list[str] = []
    if action_hits:
        suggestions.append("先看适用对象、申报条件和办理入口。")
    if material_hits:
        suggestions.append("优先整理材料清单、证照和证明附件。")
    if time_hits:
        suggestions.append("重点核对截止时间、有效期和受理窗口。")
    if risk_hits:
        suggestions.append("留意不予受理、处罚、逾期责任等约束条款。")
    if not suggestions:
        suggestions.append("先浏览摘要和知识图谱，确认是否需要收藏或后续办理。")

    if final_score >= 75:
        summary = f"这份文档与您的{profile_label}画像高度相关，建议优先处理。"
    elif final_score >= 55:
        summary = f"这份文档对您的{profile_label}画像有较明显价值，建议重点阅读。"
    elif final_score >= 35:
        summary = f"这份文档与您的{profile_label}画像存在部分关联，适合收藏备查。"
    else:
        summary = f"这份文档对您的{profile_label}画像直接匹配度一般，可按需浏览。"

    return {
        "score": final_score,
        "level": level,
        "level_label": level_label,
        "priority_label": priority_label,
        "summary": summary,
        "profile_label": profile_label,
        "matched_keywords": matched_keywords,
        "reasons": reasons[:3],
        "suggestions": suggestions[:3],
        "score_breakdown": {
            key: round(score, 3)
            for key, (score, _) in weighted_scores.items()
        },
    }
