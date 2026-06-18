"""
自然语言转 SQL 查询接口
支持两种模式：
1. 关键字匹配（默认，无需 API Key）
2. LLM 翻译（需配置 API Key）
"""
import re
from app.database import query_all, query_one
from app import queries


# ============================================================
# 模式一：关键字匹配规则引擎
# ============================================================

# 专业名映射（处理简称/别名）
MAJOR_ALIAS = {
    "金融学": "金融学", "金融": "金融学",
    "会计学": "会计学", "会计": "会计学",
    "经济统计学": "经济统计学",
    "法学": "法学", "法律": "法学",
    # 经济学保持原名（两校各有一个）
    "经济学": "经济学",
}

UNIVERSITY_ALIAS = {
    "西南财经大学": "西南财经大学", "西南财经": "西南财经大学", "西财": "西南财经大学",
    "上海财经大学": "上海财经大学", "上海财经": "上海财经大学", "上财": "上海财经大学",
}

# 查询意图模式
RULES = [
    # ---- 搜索类放最前（避免被课程名匹配拦截） ----
    {
        "pattern": r"(搜索|查找|找|搜搜|搜一搜)\s*(包含|含有|关于|含)?\s*([一-鿿\w]{2,12})",
        "handler": "global_search",
    },
    # ---- 跨校对比优先匹配 ----
    # 跨校学分对比（必须在课程对比之前，因为"学分"更长更具体）
    {
        "pattern": r"(对比|比较).*?({major}).*?学分",
        "handler": "compare_credits",
    },
    # 跨校课程对比
    {
        "pattern": r"(对比|比较).*?({major}).*?(课程|课)",
        "handler": "compare_courses",
    },
    # 共有课程
    {
        "pattern": r"(两校|西南财经.*?上海财经|上海财经.*?西南财经|西财.*?上财|上财.*?西财).*?({major}).*?(共[有同]|相同|都[有开]).*?(课程|课)?",
        "handler": "compare_common",
    },
    # 独有课程
    {
        "pattern": r"({university}).*?({major}).*?(独有|特有|独特|只有).*?(课程|课)?",
        "handler": "compare_unique",
    },
    # ---- 课程开设专业 ----
    {
        "pattern": r"(哪些|什么|哪个)\s*专业\s*(?:开设了?|开|包含|有)\s*([一-鿿\w]{2,15})(?:\s*$|\s*的|\s*课程|，|。|\?)",
        "handler": "course_majors",
    },
    # ---- 专业课程查询 ----
    {
        "pattern": r"({major}).*?(的)?\s*(必修|限选|选修)?\s*(课程|课|有哪些\s*$|有哪些\?)",
        "handler": "major_courses",
    },
    {
        "pattern": r"(查询|查看|列出|显示)\s*({major}).*?(必修|选修|限选)?.*?(课程|课)",
        "handler": "major_courses",
    },
    # ---- 学分统计 ----
    {
        "pattern": r"({major}).*?(多少|总|毕业).*?学分",
        "handler": "major_credits",
    },
    # ---- 学院概览 ----
    {
        "pattern": r"({school})\s*(学院|系)\s*(有|有哪些|多少|几个|什么).*?专业",
        "handler": "school_overview",
    },
    # ---- 课程信息查询（放最后） ----
    {
        "pattern": r"([一-鿿\w]{2,12})\s*(多少|几|什么|有没有|有没有).*?(学分|学时)",
        "handler": "course_search",
    },
]


def match_intent(text: str):
    """匹配用户的自然语言问题到查询意图"""
    text = text.strip().rstrip("？?。.")

    for rule in RULES:
        # 构建正则，替换占位符
        pattern = rule["pattern"]

        # 替换专业名占位符
        major_pattern = "|".join(re.escape(k) for k in MAJOR_ALIAS.keys())
        pattern = pattern.replace("{major}", f"({major_pattern})")

        # 替换大学名占位符
        uni_pattern = "|".join(re.escape(k) for k in UNIVERSITY_ALIAS.keys())
        pattern = pattern.replace("{university}", f"({uni_pattern})")

        # 替换学院名占位符
        school_pattern = r"(金融|经济|会计|统计|法)"
        pattern = pattern.replace("{school}", school_pattern)

        # 替换关键词占位符（课程名）
        pattern = pattern.replace(
            "{keyword}", r"([一-鿿\w]{2,15})"
        )

        m = re.search(pattern, text)
        if m:
            groups = m.groups()
            return {"handler": rule["handler"], "groups": groups, "text": text}

    return None


def resolve_entity(value: str, entity_type: str) -> str:
    """将别名解析为标准名称"""
    if entity_type == "major":
        for alias, std in MAJOR_ALIAS.items():
            if alias in value:
                return std
    elif entity_type == "university":
        for alias, std in UNIVERSITY_ALIAS.items():
            if alias in value:
                return std
    elif entity_type == "school":
        school_map = {
            "金融": "金融学院", "经济": "经济学院",
            "会计": "会计学院", "统计": "统计学院",
            "法": "法学院",
        }
        for k, v in school_map.items():
            if k in value:
                return v
    return value


def execute_intent(intent: dict) -> dict:
    """执行匹配到的查询意图"""
    handler = intent["handler"]
    groups = list(intent["groups"])

    if handler == "major_courses":
        major = resolve_entity(groups[0], "major")
        req_type = None
        for g in groups[1:]:
            if g and any(kw in g for kw in ["必修", "选修", "限选"]):
                req_type = g
                break
        data = queries.get_required_courses(major) if req_type == "必修" else (
            query_all("""
                SELECT c.code, c.name, c.credits, c.hours,
                       mc.suggested_semester, mc.requirement_type, cc.name AS category
                FROM major m
                JOIN major_course mc ON m.id = mc.major_id
                JOIN course c ON mc.course_id = c.id
                LEFT JOIN course_category cc ON c.category_id = cc.id
                WHERE m.name = ?
                ORDER BY mc.suggested_semester, c.name
            """, (major,))
        )
        result_type = "专业课程列表"
        query_desc = f"查询 {major} 的{'必修课' if req_type == '必修' else '全部课程'}"

    elif handler == "course_search":
        # groups: ("高等数学", "多少", "学分") → 取第一个即课程名
        keyword = groups[0]
        data = queries.search_course(keyword)
        result_type = "课程信息"
        query_desc = f"搜索课程「{keyword}」"

    elif handler == "major_credits":
        major = resolve_entity(groups[0], "major")
        data = [queries.get_total_credits(major)]
        result_type = "学分统计"
        query_desc = f"查询 {major} 的学分要求"

    elif handler == "course_majors":
        keyword = groups[-1] if groups else groups[0]
        data = queries.get_majors_by_course(keyword)
        result_type = "课程开设范围"
        query_desc = f"查询开设「{keyword}」的专业"

    elif handler == "school_overview":
        school = resolve_entity(groups[0], "school")
        data = queries.get_school_overview(school)
        result_type = "学院概览"
        query_desc = f"查询 {school} 的培养方案概览"

    elif handler == "compare_courses":
        major = resolve_entity(
            next((g for g in groups if any(a in g for a in MAJOR_ALIAS)), groups[0]),
            "major",
        )
        data = queries.compare_major_courses(major)
        result_type = "跨校课程对比"
        query_desc = f"对比两校 {major} 的课程设置"

    elif handler == "compare_credits":
        major = resolve_entity(
            next((g for g in groups if any(a in g for a in MAJOR_ALIAS)), groups[0]),
            "major",
        )
        data = queries.compare_credits_by_major(major)
        result_type = "跨校学分对比"
        query_desc = f"对比两校 {major} 的学分要求"

    elif handler == "compare_common":
        major = resolve_entity(
            next((g for g in groups if any(a in g for a in MAJOR_ALIAS)), groups[0]),
            "major",
        )
        data = queries.get_common_courses(major)
        result_type = "两校共有课程"
        query_desc = f"查询两校 {major} 的共有课程"

    elif handler == "global_search":
        # 取最后一个长度>=2的非停用词组，去掉末尾"的课程"
        keyword = next((g for g in reversed(groups) if g and len(g) >= 2 and g not in ["搜索", "查找", "找", "包含", "含有", "含", "关于"]), groups[-1])
        keyword = re.sub(r'(的课程|的课|课程|课)\s*$', '', keyword)
        data = queries.search_course_by_keyword(keyword, 20)
        result_type = "全局搜索"
        query_desc = f"全局搜索课程「{keyword}」"

    elif handler == "compare_unique":
        university = resolve_entity(
            next((g for g in groups if any(a in g for a in UNIVERSITY_ALIAS)), ""),
            "university",
        )
        major = resolve_entity(
            next((g for g in groups if any(a in g for a in MAJOR_ALIAS)), groups[0]),
            "major",
        )
        data = queries.get_unique_courses(major, university)
        result_type = "独有课程"
        query_desc = f"查询 {university} {major} 的独有课程"

    else:
        data = []
        result_type = "未知"
        query_desc = intent["text"]

    return {
        "query_type": result_type,
        "query_desc": query_desc,
        "result_count": len(data),
        "data": data,
    }


# ============================================================
# 模式二：LLM 翻译接口（可选，需配置 API Key）
# ============================================================

LLM_API_KEY = None  # 设置你的 API Key
LLM_API_URL = "https://api.anthropic.com/v1/messages"
LLM_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """你是一个将自然语言转换为 SQL 的助手。数据库包含以下表：

university(id, name, abbreviation)
school(id, name, university_id)
major(id, name, school_id, degree_type, total_credits, description)
course(id, code, name, credits, hours, category_id)
course_category(id, name, description)
major_course(id, major_id, course_id, requirement_type, suggested_semester)

用户用中文提问，你需要：
1. 理解用户意图
2. 生成对应的 SQLite 查询语句
3. 只返回 JSON 格式：{"sql": "SELECT ...", "explanation": "解释"}

可用查询函数：
- queries.get_required_courses("专业名") — 必修课列表
- queries.search_course("关键词") — 课程搜索
- queries.get_total_credits("专业名") — 学分统计
- queries.get_majors_by_course("关键词") — 课程开设专业
- queries.get_school_overview("学院名") — 学院概览
- queries.compare_major_courses("专业名") — 跨校课程对比
- queries.compare_credits_by_major("专业名") — 跨校学分对比
- queries.get_common_courses("专业名") — 共有课程
- queries.get_unique_courses("专业名", "大学名") — 独有课程

请根据用户问题选择最合适的查询函数并生成调用参数，返回 JSON：
{"function": "函数名", "params": ["参数1", "参数2"], "explanation": "中文解释"}
千万不要自己编造 SQL，直接用上面列出的函数。
"""


def llm_translate(question: str) -> dict:
    """使用 LLM 将自然语言转换为查询调用（需 API Key）"""
    if not LLM_API_KEY:
        return {"error": "未配置 LLM API Key，请使用关键字匹配模式"}

    try:
        import requests
        resp = requests.post(
            LLM_API_URL,
            headers={
                "x-api-key": LLM_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "max_tokens": 300,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": question}],
            },
            timeout=15,
        )
        data = resp.json()
        content = data["content"][0]["text"]

        # 解析 LLM 返回的 JSON
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            call = json.loads(json_match.group())
            func_name = call.get("function", "")
            params = call.get("params", [])
            explanation = call.get("explanation", content)

            # 动态调用查询函数
            if hasattr(queries, func_name):
                result = getattr(queries, func_name)(*params)
                return {
                    "query_type": func_name,
                    "query_desc": explanation,
                    "result_count": len(result) if isinstance(result, list) else 1,
                    "data": result,
                    "powered_by": "LLM (Claude)",
                }
    except Exception as e:
        return {"error": f"LLM 调用失败: {str(e)}"}

    return {"error": "无法解析 LLM 返回结果"}
