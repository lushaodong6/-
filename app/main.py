"""
培养方案数据库系统 - FastAPI Web 接口
提供 RESTful API 和 Swagger 文档
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from app import queries

app = FastAPI(
    title="培养方案数据库系统",
    description="西南财经大学 & 上海财经大学 本科培养方案查询与跨校对比系统",
    version="1.0.0",
)


# ========== 首页 ==========
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>培养方案数据库系统</title>
    <style>
        :root {
            --bg: #fafbfc;
            --card-bg: #ffffff;
            --text: #24292e;
            --text-secondary: #586069;
            --border: #e1e4e8;
            --accent: #0366d6;
            --accent-light: #f1f8ff;
            --green: #28a745;
            --green-bg: #f0fff4;
            --orange: #f66a0a;
            --orange-bg: #fff8f2;
            --radius: 8px;
            --shadow: 0 1px 3px rgba(27,31,35,0.04), 0 0 0 1px rgba(27,31,35,0.04);
            --shadow-hover: 0 4px 12px rgba(27,31,35,0.08), 0 0 0 1px rgba(27,31,35,0.06);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            color: var(--text);
            background: var(--bg);
            line-height: 1.6;
        }

        .container { max-width: 960px; margin: 0 auto; padding: 32px 20px 60px; }

        /* Header */
        header {
            padding: 28px 0 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }
        header h1 {
            font-size: 26px;
            font-weight: 600;
            letter-spacing: -0.3px;
            color: var(--text);
        }
        header .subtitle {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        /* Section titles */
        .section-title {
            font-size: 17px;
            font-weight: 600;
            margin: 36px 0 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-title .dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--accent);
        }
        .tag {
            font-size: 11px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 12px;
            background: var(--green-bg);
            color: var(--green);
        }

        /* Cards grid */
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }

        /* Card */
        .card {
            background: var(--card-bg);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            text-decoration: none;
            color: inherit;
            transition: box-shadow 0.15s ease, transform 0.1s ease;
            display: flex;
            flex-direction: column;
        }
        .card:hover {
            box-shadow: var(--shadow-hover);
            transform: translateY(-1px);
        }
        .card .icon {
            width: 32px; height: 32px;
            border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
            margin-bottom: 10px;
            flex-shrink: 0;
        }
        .card .icon.blue   { background: #e8f0fe; color: #1a73e8; }
        .card .icon.green  { background: #e6f4ea; color: #1e8e3e; }
        .card .icon.orange { background: #fef7e0; color: #e37400; }
        .card .icon.purple { background: #f3e8fd; color: #9334e6; }
        .card .icon.teal   { background: #e0f2f1; color: #00796b; }
        .card .icon.pink   { background: #fce4ec; color: #c62828; }

        .card h3 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
            color: var(--text);
        }
        .card p {
            font-size: 12.5px;
            color: var(--text-secondary);
            margin-bottom: 10px;
            flex: 1;
        }
        .card .endpoint {
            font-family: "SF Mono", "Fira Code", "Consolas", monospace;
            font-size: 11.5px;
            color: var(--accent);
            background: var(--accent-light);
            padding: 5px 10px;
            border-radius: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Data links row */
        .link-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .link-row a {
            font-size: 13px;
            padding: 7px 16px;
            border-radius: 20px;
            background: var(--card-bg);
            box-shadow: var(--shadow);
            text-decoration: none;
            color: var(--text);
            transition: all 0.15s;
        }
        .link-row a:hover {
            background: var(--accent);
            color: white;
        }

        /* Footer */
        footer {
            text-align: center;
            font-size: 12px;
            color: #aaa;
            margin-top: 48px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }

        /* Tip banner */
        .tip {
            background: var(--accent-light);
            border-radius: 6px;
            padding: 12px 16px;
            font-size: 13px;
            color: var(--accent);
            margin-bottom: 28px;
            display: flex; align-items: center; gap: 8px;
        }
        .tip a { color: var(--accent); font-weight: 600; }
    </style>
</head>
<body>
<div class="container">

<header>
    <h1>培养方案数据库系统</h1>
    <p class="subtitle">西南财经大学 &amp; 上海财经大学 2024 级本科人才培养方案</p>
</header>

<div class="tip">
    <span>💡</span> 访问 <a href="/docs">/docs</a> 进入 Swagger 交互式 API 文档，在线测试所有接口
</div>

<div class="section-title">
    <span class="dot"></span> 核心查询
</div>

<div class="cards">
    <a class="card" href="/api/major/金融学/courses?requirement_type=必修">
        <span class="icon blue">📋</span>
        <h3>专业必修课列表</h3>
        <p>按专业名称查询全部必修课程，返回学分、学时、开课学期</p>
        <span class="endpoint">GET /api/major/{name}/courses</span>
    </a>

    <a class="card" href="/api/course/search?keyword=经济学">
        <span class="icon green">🔍</span>
        <h3>课程信息检索</h3>
        <p>关键词搜索课程，查看代码、学分、学时、所属类别</p>
        <span class="endpoint">GET /api/course/search?keyword=</span>
    </a>

    <a class="card" href="/api/major/金融学/credits">
        <span class="icon orange">📊</span>
        <h3>专业学分统计</h3>
        <p>查看某专业毕业总学分要求，按必修 / 限选 / 选修分类汇总</p>
        <span class="endpoint">GET /api/major/{name}/credits</span>
    </a>

    <a class="card" href="/api/course/计量经济学/majors">
        <span class="icon purple">🏫</span>
        <h3>课程覆盖范围</h3>
        <p>查询某门课程被哪些专业开设，跨校跨学院检索</p>
        <span class="endpoint">GET /api/course/{name}/majors</span>
    </a>

    <a class="card" href="/api/school/金融学院/overview">
        <span class="icon teal">📈</span>
        <h3>学院培养方案概览</h3>
        <p>查询某学院下所有专业的课程数量与学分结构一览</p>
        <span class="endpoint">GET /api/school/{name}/overview</span>
    </a>

    <a class="card" href="/api/course/fullsearch?keyword=数学">
        <span class="icon pink">🔎</span>
        <h3>全局课程搜索</h3>
        <p>按关键词模糊匹配，按覆盖专业数量排序返回结果</p>
        <span class="endpoint">GET /api/course/fullsearch?keyword=</span>
    </a>
</div>

<div class="section-title">
    <span class="dot"></span> 跨校对比 <span class="tag">子模块 B</span>
</div>

<div class="cards">
    <a class="card" href="/api/compare/major/金融学/courses">
        <span class="icon blue">📚</span>
        <h3>课程设置对比</h3>
        <p>并排对比两校同专业的所有课程安排</p>
        <span class="endpoint">GET /api/compare/major/{name}/courses</span>
    </a>

    <a class="card" href="/api/compare/major/金融学/credits">
        <span class="icon green">📐</span>
        <h3>学分结构对比</h3>
        <p>比较两校同专业学分要求、必修选修比例差异</p>
        <span class="endpoint">GET /api/compare/major/{name}/credits</span>
    </a>

    <a class="card" href="/api/compare/major/会计学/common">
        <span class="icon orange">🤝</span>
        <h3>共有课程</h3>
        <p>找出两校同专业都开设的课程，分析培养方案重叠度</p>
        <span class="endpoint">GET /api/compare/major/{name}/common</span>
    </a>

    <a class="card" href="/api/compare/major/经济学/unique?university=SWUFE">
        <span class="icon purple">⭐</span>
        <h3>独有课程</h3>
        <p>查看某校某专业独有的课程，发现培养方案差异化</p>
        <span class="endpoint">GET /api/compare/major/{name}/unique</span>
    </a>
</div>

<div class="section-title">
    <span class="dot"></span> 基础数据
</div>

<div class="link-row">
    <a href="/api/universities">🏛 大学列表</a>
    <a href="/api/schools">🏢 学院列表</a>
    <a href="/api/majors">🎓 专业列表</a>
</div>

<footer>
    培养方案数据库系统 · 数据库课程作业 · 题目三
</footer>

</div>
</body>
</html>
"""


# ========== 基础数据接口 ==========
@app.get("/api/universities", tags=["基础数据"])
def api_universities():
    """获取所有大学列表"""
    return queries.list_universities()


@app.get("/api/schools", tags=["基础数据"])
def api_schools(university_id: int = Query(None, description="按大学ID筛选")):
    """获取所有学院列表"""
    return queries.list_schools(university_id)


@app.get("/api/majors", tags=["基础数据"])
def api_majors(
    school_id: int = Query(None, description="按学院ID筛选"),
    university_id: int = Query(None, description="按大学ID筛选"),
):
    """获取所有专业列表"""
    return queries.list_majors(school_id, university_id)


# ========== 查询1：专业必修课列表 ==========
@app.get("/api/major/{major_name}/courses", tags=["专业查询"])
def api_major_courses(
    major_name: str,
    requirement_type: str = Query(None, description="课程要求类型：必修/限选/选修"),
):
    """
    查询某专业的课程列表
    - 默认返回所有课程
    - 可通过 requirement_type 筛选必修/限选/选修
    """
    if requirement_type == "必修":
        return queries.get_required_courses(major_name)
    from app.database import query_all
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
    return query_all(sql, params)


# ========== 查询2：课程信息查询 ==========
@app.get("/api/course/search", tags=["课程查询"])
def api_course_search(keyword: str = Query(..., description="课程名称关键词")):
    """根据关键词搜索课程，返回课程代码、名称、学分、学时、类别"""
    return queries.search_course(keyword)


# ========== 查询3：专业学分统计 ==========
@app.get("/api/major/{major_name}/credits", tags=["专业查询"])
def api_major_credits(major_name: str):
    """查询某专业的总学分要求（分必修/限选/选修统计）"""
    result = queries.get_total_credits(major_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}'")
    return result


# ========== 查询4：课程-专业关联 ==========
@app.get("/api/course/{keyword}/majors", tags=["课程查询"])
def api_course_majors(keyword: str):
    """查询开设某门课程（模糊匹配）的所有专业"""
    result = queries.get_majors_by_course(keyword)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到包含 '{keyword}' 的课程")
    return result


# ========== 查询5：学院概览 ==========
@app.get("/api/school/{school_name}/overview", tags=["学院查询"])
def api_school_overview(school_name: str):
    """查询某学院下所有专业的培养方案概况"""
    result = queries.get_school_overview(school_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到学院 '{school_name}'")
    return result


# ========== 查询6：全局模糊搜索 ==========
@app.get("/api/course/fullsearch", tags=["课程查询"])
def api_course_fullsearch(
    keyword: str = Query(..., description="课程名称关键词"),
    limit: int = Query(20, description="返回结果数量上限"),
):
    """全局模糊搜索课程，按覆盖专业数排序"""
    return queries.search_course_by_keyword(keyword, limit)


# ========== 子模块B：跨校对比 ==========
@app.get("/api/compare/major/{major_name}/courses", tags=["跨校对比"])
def api_compare_courses(major_name: str):
    """对比两校同专业的课程设置"""
    result = queries.compare_major_courses(major_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}'")
    return result


@app.get("/api/compare/major/{major_name}/credits", tags=["跨校对比"])
def api_compare_credits(major_name: str):
    """对比两校同专业的学分要求"""
    result = queries.compare_credits_by_major(major_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}'")
    return result


@app.get("/api/compare/major/{major_name}/common", tags=["跨校对比"])
def api_compare_common(major_name: str):
    """查询两校同专业共有的课程"""
    result = queries.get_common_courses(major_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到专业 '{major_name}' 的共有课程")
    return result


@app.get("/api/compare/major/{major_name}/unique", tags=["跨校对比"])
def api_compare_unique(
    major_name: str,
    university: str = Query("SWUFE", description="大学缩写：SWUFE 或 SUFE"),
):
    """查询某校某专业独有的课程"""
    result = queries.get_unique_courses(major_name, university)
    return result
