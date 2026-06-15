"""
培养方案数据库系统 - FastAPI Web 接口
浏览器访问 → HTML 表格渲染
Swagger/API 调用 → JSON 返回
"""
import json
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from app import queries
from app.database import query_all

app = FastAPI(
    title="培养方案数据库系统",
    description="西南财经大学 & 上海财经大学 本科培养方案查询与跨校对比系统",
    version="1.0.0",
)

# ============================================================
# 通用工具：根据请求自动选择 HTML 或 JSON 响应
# ============================================================
def wants_html(request: Request) -> bool:
    """检测请求是否来自浏览器"""
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def json_or_html(request: Request, data, title="查询结果", columns=None):
    """浏览器返回 HTML 表格，否则返回 JSON"""
    if wants_html(request):
        if isinstance(data, dict):
            data = [data]
        if not data:
            return wrap_html(f"<h2>{title}</h2><p class='empty'>无匹配结果</p>", title)
        # 自动推断列
        if columns is None:
            columns = list(data[0].keys())
        return wrap_html(render_table(data, title, columns), title)
    return data


def wrap_html(body: str, title="查询结果") -> HTMLResponse:
    """统一 HTML 页面外壳"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - 培养方案数据库</title>
<style>
    :root {{
        --bg: #fafbfc; --card-bg: #fff; --text: #24292e;
        --text-secondary: #586069; --border: #e1e4e8;
        --accent: #0366d6; --accent-light: #f1f8ff;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
        color: var(--text); background: var(--bg); line-height: 1.6;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px 60px; }}
    .back {{ display: inline-block; font-size: 13px; color: var(--accent); text-decoration: none; margin-bottom: 18px; }}
    .back:hover {{ text-decoration: underline; }}
    h2 {{ font-size: 20px; font-weight: 600; margin-bottom: 4px; }}
    .count {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 16px; }}
    .empty {{ color: var(--text-secondary); font-size: 14px; margin-top: 20px; }}

    table {{
        width: 100%; border-collapse: collapse; background: var(--card-bg);
        border-radius: 6px; overflow: hidden;
        box-shadow: 0 1px 3px rgba(27,31,35,0.04), 0 0 0 1px rgba(27,31,35,0.04);
        font-size: 13.5px;
    }}
    thead {{ background: #f6f8fa; }}
    th {{
        text-align: left; padding: 10px 14px; font-weight: 600;
        color: var(--text-secondary); border-bottom: 1px solid var(--border);
        white-space: nowrap;
    }}
    td {{
        padding: 9px 14px; border-bottom: 1px solid #f0f0f0;
        color: var(--text);
    }}
    tr:hover td {{ background: #fafbfc; }}
    tr:last-child td {{ border-bottom: none; }}

    .badge {{
        display: inline-block; padding: 2px 8px; border-radius: 10px;
        font-size: 11.5px; font-weight: 500;
    }}
    .badge-required {{ background: #fee9e9; color: #c62828; }}
    .badge-limited {{ background: #fff3e0; color: #e65100; }}
    .badge-elective {{ background: #e8f5e9; color: #2e7d32; }}
    .badge-swufe {{ background: #e3f2fd; color: #1565c0; }}
    .badge-sufe  {{ background: #fce4ec; color: #880e4f; }}

    .highlight {{ color: var(--accent); font-weight: 600; }}

    @media (max-width: 768px) {{
        table {{ font-size: 12px; }}
        th, td {{ padding: 7px 8px; }}
    }}
</style>
</head>
<body>
<div class="container">
    <a class="back" href="/">&larr; 返回首页</a>
    {body}
</div>
</body>
</html>"""
    return HTMLResponse(content=html)


def render_table(rows: list, title: str, columns: list) -> str:
    """渲染数据为 HTML 表格"""
    # 列中文映射
    col_labels = {
        "name": "名称", "code": "代码", "credits": "学分", "hours": "学时",
        "category": "课程类别", "requirement_type": "修读要求",
        "suggested_semester": "开课学期", "major_name": "专业名称",
        "school_name": "学院", "university_name": "大学", "university": "大学",
        "abbreviation": "缩写", "id": "ID", "total_credits": "毕业总学分",
        "required_credits": "必修学分", "limited_elective_credits": "限选学分",
        "elective_credits": "选修学分", "all_credits": "总学分合计",
        "limited_elective": "限选学分", "course_count": "课程数量",
        "major_count": "覆盖专业数", "degree_type": "学位类型",
        "description": "描述", "universities": "开设院校",
        "required_total": "毕业要求总学分",
    }

    header = "".join(f"<th>{col_labels.get(c, c)}</th>" for c in columns)

    body_rows = ""
    for row in rows:
        cells = ""
        for c in columns:
            v = row.get(c, "")
            if v is None:
                v = "-"
            # 修读要求加颜色标签
            if c == "requirement_type":
                cls = {"必修": "badge-required", "限选": "badge-limited", "选修": "badge-elective"}.get(str(v), "")
                v = f'<span class="badge {cls}">{v}</span>' if cls else v
            # 大学缩写加颜色
            if c in ("university", "abbreviation"):
                cls = {"SWUFE": "badge-swufe", "西南财经大学": "badge-swufe",
                       "SUFE": "badge-sufe", "上海财经大学": "badge-sufe"}.get(str(v), "")
                v = f'<span class="badge {cls}">{v}</span>' if cls else v
            # 数值格式化
            if isinstance(v, float):
                v = f"{v:.1f}" if v == int(v) else f"{v:.1f}"
            cells += f"<td>{v}</td>"
        body_rows += f"<tr>{cells}</tr>"

    return f"""
    <h2>{title}</h2>
    <p class="count">共 {len(rows)} 条结果</p>
    <table><thead><tr>{header}</tr></thead><tbody>{body_rows}</tbody></table>
    """


# ============================================================
# CSS & page style (shared across all pages)
# ============================================================
CSS = """
:root {
    --bg: #fafbfc; --card-bg: #ffffff; --text: #24292e;
    --text-secondary: #586069; --border: #e1e4e8; --accent: #0366d6;
    --accent-light: #f1f8ff; --green: #28a745; --green-bg: #f0fff4;
    --radius: 8px;
    --shadow: 0 1px 3px rgba(27,31,35,0.04), 0 0 0 1px rgba(27,31,35,0.04);
    --shadow-hover: 0 4px 12px rgba(27,31,35,0.08), 0 0 0 1px rgba(27,31,35,0.06);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    color: var(--text); background: var(--bg); line-height: 1.6;
}
.container { max-width: 960px; margin: 0 auto; padding: 32px 20px 60px; }
header { padding: 28px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 32px; }
header h1 { font-size: 26px; font-weight: 600; letter-spacing: -0.3px; color: var(--text); }
header .subtitle { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.section-title { font-size: 17px; font-weight: 600; margin: 36px 0 16px; display: flex; align-items: center; gap: 8px; }
.section-title .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.tag { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 12px; background: var(--green-bg); color: var(--green); }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.card {
    background: var(--card-bg); border-radius: var(--radius); padding: 20px;
    box-shadow: var(--shadow); text-decoration: none; color: inherit;
    transition: box-shadow 0.15s ease, transform 0.1s ease;
    display: flex; flex-direction: column;
}
.card:hover { box-shadow: var(--shadow-hover); transform: translateY(-1px); }
.card .icon { width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 10px; flex-shrink: 0; }
.card .icon.blue   { background: #e8f0fe; color: #1a73e8; }
.card .icon.green  { background: #e6f4ea; color: #1e8e3e; }
.card .icon.orange { background: #fef7e0; color: #e37400; }
.card .icon.purple { background: #f3e8fd; color: #9334e6; }
.card .icon.teal   { background: #e0f2f1; color: #00796b; }
.card .icon.pink   { background: #fce4ec; color: #c62828; }
.card h3 { font-size: 14px; font-weight: 600; margin-bottom: 4px; color: var(--text); }
.card p { font-size: 12.5px; color: var(--text-secondary); margin-bottom: 10px; flex: 1; }
.card .endpoint {
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    font-size: 11.5px; color: var(--accent); background: var(--accent-light);
    padding: 5px 10px; border-radius: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.link-row { display: flex; gap: 10px; flex-wrap: wrap; }
.link-row a {
    font-size: 13px; padding: 7px 16px; border-radius: 20px;
    background: var(--card-bg); box-shadow: var(--shadow); text-decoration: none; color: var(--text); transition: all 0.15s;
}
.link-row a:hover { background: var(--accent); color: white; }
footer { text-align: center; font-size: 12px; color: #aaa; margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border); }
.tip { background: var(--accent-light); border-radius: 6px; padding: 12px 16px; font-size: 13px; color: var(--accent); margin-bottom: 28px; display: flex; align-items: center; gap: 8px; }
.tip a { color: var(--accent); font-weight: 600; }
"""


# ========== 首页 ==========
@app.get("/", response_class=HTMLResponse)
def home():
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>培养方案数据库系统</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
<header>
    <h1>培养方案数据库系统</h1>
    <p class="subtitle">西南财经大学 &amp; 上海财经大学 2024 级本科人才培养方案</p>
</header>
<div class="tip"><span>💡</span> 访问 <a href="/docs">/docs</a> 进入 Swagger 交互式 API 文档，在线测试所有接口</div>

<div class="section-title"><span class="dot"></span> 核心查询</div>
<div class="cards">
    <a class="card" href="/api/major/金融学/courses?requirement_type=必修">
        <span class="icon blue">📋</span><h3>专业必修课列表</h3>
        <p>按专业名称查询课程，支持按必修/限选/选修筛选</p>
        <span class="endpoint">GET /api/major/金融学/courses</span>
    </a>
    <a class="card" href="/api/course/search?keyword=经济学">
        <span class="icon green">🔍</span><h3>课程信息检索</h3>
        <p>关键词搜索课程，查看代码、学分、学时、所属类别</p>
        <span class="endpoint">GET /api/course/search?keyword=经济学</span>
    </a>
    <a class="card" href="/api/major/金融学/credits">
        <span class="icon orange">📊</span><h3>专业学分统计</h3>
        <p>查看毕业总学分要求，按必修/限选/选修分类汇总</p>
        <span class="endpoint">GET /api/major/金融学/credits</span>
    </a>
    <a class="card" href="/api/course/计量经济学/majors">
        <span class="icon purple">🏫</span><h3>课程覆盖范围</h3>
        <p>查询某门课程被哪些专业开设，跨校跨学院</p>
        <span class="endpoint">GET /api/course/计量经济学/majors</span>
    </a>
    <a class="card" href="/api/school/金融学院/overview">
        <span class="icon teal">📈</span><h3>学院概览</h3>
        <p>某学院下所有专业的课程数量与学分结构</p>
        <span class="endpoint">GET /api/school/金融学院/overview</span>
    </a>
    <a class="card" href="/api/course/fullsearch?keyword=数学">
        <span class="icon pink">🔎</span><h3>全局课程搜索</h3>
        <p>按关键词模糊匹配，按覆盖专业数量排序</p>
        <span class="endpoint">GET /api/course/fullsearch?keyword=数学</span>
    </a>
</div>

<div class="section-title"><span class="dot"></span> 跨校对比 <span class="tag">子模块 B</span></div>
<div class="cards">
    <a class="card" href="/api/compare/major/金融学/courses">
        <span class="icon blue">📚</span><h3>课程设置对比</h3>
        <p>并排对比两校同专业的所有课程</p>
        <span class="endpoint">GET /api/compare/major/金融学/courses</span>
    </a>
    <a class="card" href="/api/compare/major/金融学/credits">
        <span class="icon green">📐</span><h3>学分结构对比</h3>
        <p>比较两校同专业学分要求与必修选修比例</p>
        <span class="endpoint">GET /api/compare/major/金融学/credits</span>
    </a>
    <a class="card" href="/api/compare/major/会计学/common">
        <span class="icon orange">🤝</span><h3>共有课程</h3>
        <p>找出两校同专业都开设的课程</p>
        <span class="endpoint">GET /api/compare/major/会计学/common</span>
    </a>
    <a class="card" href="/api/compare/major/经济学/unique?university=SWUFE">
        <span class="icon purple">⭐</span><h3>独有课程</h3>
        <p>查看某校某专业独有的课程</p>
        <span class="endpoint">GET /api/compare/major/经济学/unique</span>
    </a>
</div>

<div class="section-title"><span class="dot"></span> 基础数据</div>
<div class="link-row">
    <a href="/api/universities">🏛 大学列表</a>
    <a href="/api/schools">🏢 学院列表</a>
    <a href="/api/majors">🎓 专业列表</a>
</div>

<footer>培养方案数据库系统 · 数据库课程作业 · 题目三</footer>
</div>
</body>
</html>"""


# ========== 基础数据 ==========
@app.get("/api/universities", tags=["基础数据"])
def api_universities(request: Request):
    data = queries.list_universities()
    return json_or_html(request, data, "大学列表")


@app.get("/api/schools", tags=["基础数据"])
def api_schools(request: Request, university_id: int = Query(None, description="按大学ID筛选")):
    data = queries.list_schools(university_id)
    title = "学院列表"
    if university_id:
        title += f" (大学ID={university_id})"
    return json_or_html(request, data, title)


@app.get("/api/majors", tags=["基础数据"])
def api_majors(
    request: Request,
    school_id: int = Query(None, description="按学院ID筛选"),
    university_id: int = Query(None, description="按大学ID筛选"),
):
    data = queries.list_majors(school_id, university_id)
    title = "专业列表"
    if school_id:
        title += f" (学院ID={school_id})"
    if university_id:
        title += f" (大学ID={university_id})"
    return json_or_html(request, data, title)


# ========== 查询1：专业课程列表 ==========
@app.get("/api/major/{major_name}/courses", tags=["专业查询"])
def api_major_courses(
    request: Request,
    major_name: str,
    requirement_type: str = Query(None, description="课程要求类型：必修/限选/选修"),
):
    if requirement_type == "必修":
        data = queries.get_required_courses(major_name)
    else:
        sql = """
            SELECT c.code, c.name, c.credits, c.hours,
                   mc.suggested_semester, mc.requirement_type,
                   cc.name AS category
            FROM major m
            JOIN major_course mc ON m.id = mc.major_id
            JOIN course c ON mc.course_id = c.id
            LEFT JOIN course_category cc ON c.category_id = cc.id
            WHERE m.name = ?
        """
        params = [major_name]
        if requirement_type:
            sql += " AND mc.requirement_type = ?"
            params.append(requirement_type)
        sql += " ORDER BY mc.suggested_semester, c.name"
        data = query_all(sql, params)

    title = f"{major_name} - 课程列表"
    if requirement_type:
        title += f" ({requirement_type})"
    return json_or_html(request, data, title)


# ========== 查询2：课程信息检索 ==========
@app.get("/api/course/search", tags=["课程查询"])
def api_course_search(request: Request, keyword: str = Query(..., description="课程名称关键词")):
    data = queries.search_course(keyword)
    return json_or_html(request, data, f"课程搜索: {keyword}")


# ========== 查询3：专业学分统计 ==========
@app.get("/api/major/{major_name}/credits", tags=["专业查询"])
def api_major_credits(request: Request, major_name: str):
    result = queries.get_total_credits(major_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}'")
    return json_or_html(request, result, f"{major_name} - 学分统计")


# ========== 查询4：课程-专业关联 ==========
@app.get("/api/course/{keyword}/majors", tags=["课程查询"])
def api_course_majors(request: Request, keyword: str):
    data = queries.get_majors_by_course(keyword)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到包含 '{keyword}' 的课程")
    return json_or_html(request, data, f"开设「{keyword}」的专业")


# ========== 查询5：学院概览 ==========
@app.get("/api/school/{school_name}/overview", tags=["学院查询"])
def api_school_overview(request: Request, school_name: str):
    data = queries.get_school_overview(school_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到学院 '{school_name}'")
    return json_or_html(request, data, f"{school_name} - 培养方案概览")


# ========== 查询6：全局模糊搜索 ==========
@app.get("/api/course/fullsearch", tags=["课程查询"])
def api_course_fullsearch(
    request: Request,
    keyword: str = Query(..., description="课程名称关键词"),
    limit: int = Query(20, description="返回结果数量上限"),
):
    data = queries.search_course_by_keyword(keyword, limit)
    return json_or_html(request, data, f"全局搜索: {keyword}")


# ========== 子模块B：跨校对比 ==========
@app.get("/api/compare/major/{major_name}/courses", tags=["跨校对比"])
def api_compare_courses(request: Request, major_name: str):
    data = queries.compare_major_courses(major_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}'")
    return json_or_html(request, data, f"跨校课程对比: {major_name}")


@app.get("/api/compare/major/{major_name}/credits", tags=["跨校对比"])
def api_compare_credits(request: Request, major_name: str):
    data = queries.compare_credits_by_major(major_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}'")
    return json_or_html(request, data, f"跨校学分对比: {major_name}")


@app.get("/api/compare/major/{major_name}/common", tags=["跨校对比"])
def api_compare_common(request: Request, major_name: str):
    data = queries.get_common_courses(major_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}' 的共有课程")
    return json_or_html(request, data, f"两校共有课程: {major_name}")


@app.get("/api/compare/major/{major_name}/unique", tags=["跨校对比"])
def api_compare_unique(
    request: Request,
    major_name: str,
    university: str = Query("SWUFE", description="大学缩写：SWUFE 或 SUFE"),
):
    data = queries.get_unique_courses(major_name, university)
    uni_name = "西南财经大学" if university == "SWUFE" else "上海财经大学"
    return json_or_html(request, data, f"{uni_name}独有课程: {major_name}")
