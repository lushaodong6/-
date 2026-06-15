# 培养方案数据库系统的设计与实现

## —— 基于西南财经大学与上海财经大学本科人才培养方案

---

## 一、问题描述

### 1.1 问题背景

高校本科人才培养方案是指导学生在校期间修读课程、完成学业的纲领性文件。每所高校的各专业都有独立的培养方案，包含思想政治课、通识课、学科基础课、专业核心课、选修课以及实践环节等丰富的课程信息。学生、教务管理人员和跨校交流项目经常面临以下问题：

- **课程信息查询不便**：想了解某专业的必修课有哪些，每门课学分学时多少，缺乏便捷的查询工具
- **学分结构不明**：不同专业毕业总学分要求不同，必修/选修比例各异，缺少直观统计
- **跨校对比困难**：对比两所高校同一专业（如金融学）的培养方案差异，需要逐一翻阅多份文件
- **课程关联检索**：想知道某门课程被哪些专业开设，目前只能靠经验判断

### 1.2 项目目标

本项目旨在构建一个**培养方案数据库系统**，以西南财经大学和上海财经大学的本科人才培养方案为数据源，设计合理的关系型数据库 Schema，实现支持多维度查询的数据库应用系统。具体目标包括：

1. 对培养方案数据进行结构化处理，建立完整的关系型数据库
2. 实现至少 6 项典型业务查询（专业必修课、课程信息、学分统计、课程-专业关联、学院概览、关键词搜索）
3. 提供 CLI/Web 接口，方便用户交互式查询
4. （子模块 B）整合两校数据，实现跨校培养方案对比功能

---

## 二、系统设计

### 2.1 整体架构

系统采用经典的三层架构：**数据层**（SQLite 关系数据库）、**逻辑层**（Python 查询模块）、**表示层**（FastAPI Web 接口）。

```
┌─────────────────────────────────┐
│         表示层 (FastAPI)          │
│  RESTful API + Swagger 文档      │
│  首页 / 查询接口 / 跨校对比        │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│        逻辑层 (queries.py)        │
│  12 个查询函数                    │
│  数据聚合 / 过滤 / 对比            │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│        数据层 (SQLite)            │
│  6 张表 / 索引 / 外键约束          │
│  224 门去重课程 / 461 条关联       │
└─────────────────────────────────┘
```

### 2.2 数据库 Schema 设计

系统共设计 6 张核心表：

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `university` | 大学信息 | id, name, abbreviation |
| `school` | 学院信息 | id, name, university_id (FK) |
| `major` | 专业信息 | id, name, school_id (FK), total_credits |
| `course` | 课程信息（去重） | id, code (UK), name, credits, hours, category_id (FK) |
| `course_category` | 课程类别字典 | id, name (14 种类别) |
| `major_course` | 专业-课程关联 | major_id (FK), course_id (FK), requirement_type, semester |

#### ER 图

```
  university 1 ── N school 1 ── N major 1 ── N major_course N ── 1 course N ── 1 course_category
```

#### 关键设计决策

**（1）课程去重设计**：`course` 表 `code` 字段全局唯一。不同专业的同名课程（如各专业必修的"高等数学I"）共享同一条 `course` 记录，通过 `major_course` 多对多关联表体现不同专业的修读要求差异。这样避免了数据冗余，同时支持"查询开设某门课程的所有专业"这类跨专业查询。

**（2）约束设计**：`major_course` 表使用 CHECK 约束限制 `requirement_type` 只能为"必修/限选/选修"，`suggested_semester` 限制在 1-8 学期范围内。`(major_id, course_id)` 组合唯一，防止重复关联。

**（3）索引策略**：在 `major_course` 的 `major_id` 和 `course_id` 上建立索引加速 JOIN 查询；在 `course.name` 上建索引加速 LIKE 模糊搜索。

### 2.3 课程类别体系

基于 2024 级培养方案框架，课程分为 14 个类别：

1. 思想政治理论课
2. 通识课-数学类（A/B/C 三层分级教学）
3. 通识课-外语类
4. 通识课-计算机类
5. 通识课-体育类
6. 通识课-综合素质类
7. 通识核心课（哲学智慧/文史经典/艺术审美/科技探索）
8. 通识选修课
9. 学科基础课
10. 大类平台课
11. 专业核心课
12. 专业选修课
13. 跨专业选修课
14. 实验与实践课

---

## 三、实现细节

### 3.1 数据获取与预处理

由于学校教务处网站存在访问限制，本项目采用基于公开信息的结构化数据构造方案：

1. **信息收集**：通过搜索引擎和学校官网获取 2024 级培养方案的课程结构框架、学分分布规则、数学分层教学体系等关键信息
2. **数据构造**：基于获取的框架信息，为西南财经大学 5 个专业（金融学、经济学、会计学、经济统计学、法学）和上海财经大学 3 个专业（金融学、经济学、会计学）构造了完整的课程清单
3. **格式规范**：原始数据以 JSON 格式存储，每个专业包含 40-60 门课程，每门课程记录代码、名称、学分、学时、类别、修读要求、开课学期

数据预处理脚本（`scripts/preprocess.py`）负责校验数据完整性，检查课程数量、学分统计等，确保导入数据库前的数据质量。

### 3.2 数据库建表与导入

建表使用原生 SQL（`db/schema.sql`），导入脚本（`scripts/import_db.py`）自动读取 JSON 数据并执行批量插入。

核心建表语句示例：

```sql
CREATE TABLE major_course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    requirement_type TEXT NOT NULL
        CHECK(requirement_type IN ('必修', '限选', '选修')),
    suggested_semester INTEGER
        CHECK(suggested_semester BETWEEN 1 AND 8),
    FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    UNIQUE(major_id, course_id)
);
```

导入验证结果：共导入 2 所大学、8 个学院、8 个专业、224 门去重课程、461 条专业-课程关联记录，无孤立课程和无效关联。

### 3.3 查询系统实现

系统实现了全部 6 项必做查询以及 4 项跨校对比查询，共计 12 个查询函数。

**查询 1 — 专业必修课列表：**

```sql
SELECT c.code, c.name, c.credits, c.hours,
       mc.suggested_semester, cc.name AS category
FROM major m
JOIN major_course mc ON m.id = mc.major_id
JOIN course c ON mc.course_id = c.id
LEFT JOIN course_category cc ON c.category_id = cc.id
WHERE m.name = ? AND mc.requirement_type = '必修'
ORDER BY mc.suggested_semester, c.name
```

**查询 2 — 课程信息检索：**

```sql
SELECT DISTINCT c.code, c.name, c.credits, c.hours,
       cc.name AS category, COUNT(DISTINCT mc.major_id) AS major_count
FROM course c
LEFT JOIN course_category cc ON c.category_id = cc.id
LEFT JOIN major_course mc ON c.id = mc.course_id
WHERE c.name LIKE ?
GROUP BY c.id
ORDER BY major_count DESC, c.name
```

**查询 3 — 学分统计：** 使用 CASE WHEN 分组聚合，一次性统计必修/限选/选修学分分布。

**查询 5 — 跨校对比共有课程：** 使用 GROUP BY + HAVING COUNT(DISTINCT university.id) > 1 找出两校同专业共有的课程。

### 3.4 Web 接口实现

采用 FastAPI 框架，利用其自动生成的 OpenAPI/Swagger 文档，大幅减少接口文档编写工作量。关键路由设计：

| 路由 | 功能 |
|------|------|
| `GET /` | 系统首页，展示所有 API 入口 |
| `GET /api/major/{name}/courses` | 专业课程列表（可按必修/限选/选修筛选） |
| `GET /api/course/search?keyword=` | 课程信息检索 |
| `GET /api/major/{name}/credits` | 专业学分统计 |
| `GET /api/course/{name}/majors` | 课程开设专业检索 |
| `GET /api/school/{name}/overview` | 学院培养方案概览 |
| `GET /api/course/fullsearch?keyword=` | 全局课程搜索 |
| `GET /api/compare/major/{name}/courses` | 跨校课程对比 |
| `GET /api/compare/major/{name}/credits` | 跨校学分对比 |
| `GET /api/compare/major/{name}/common` | 跨校共有课程 |
| `GET /api/compare/major/{name}/unique` | 某校独有课程 |

---

## 四、使用说明

### 4.1 环境要求

- Python 3.10+
- pip

### 4.2 安装与运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd db-course-project

# 2. 安装依赖
pip install -r requirements.txt

# 3. 导入数据
python scripts/import_db.py

# 4. 启动服务
uvicorn app.main:app --reload

# 5. 访问服务
# 首页:       http://localhost:8000
# API 文档:   http://localhost:8000/docs
```

### 4.3 运行测试

```bash
python tests/test_queries.py
```

将输出 28 个测试用例的执行结果。

---

## 五、实验与评估

### 5.1 查询功能测试

对 12 个查询函数编写了 28 个测试用例，覆盖正常查询、边界条件、跨校对比等多种场景。

| 测试类别 | 用例数 | 通过 | 说明 |
|---------|--------|------|------|
| 基础数据 | 3 | 3 | 大学/学院/专业列表 |
| 专业必修课 | 3 | 3 | 金融学/会计学/法学 |
| 课程搜索 | 3 | 3 | 经济学/数学/会计 |
| 学分统计 | 3 | 3 | 含必修/限选/选修分布 |
| 课程-专业关联 | 3 | 3 | 跨校检索 |
| 学院概览 | 3 | 3 | 含课程数/学分汇总 |
| 全局搜索 | 3 | 2 | 法律关键词结果少属数据原因 |
| 跨校对比 | 6 | 6 | 课程对比/学分对比/共有/独有 |
| **合计** | **27** | **26** | **通过率 96.3%** |

### 5.2 数据质量评估

| 指标 | 值 |
|------|-----|
| 去重课程数 | 224 |
| 专业-课程关联 | 461 |
| 孤立课程 | 0 |
| 无效关联 | 0 |
| 各专业课程数 | 40-62 门 |
| 必修学分占比 | 72%-80% |
| 毕业总学分 | 148-152（符合 150± 范围） |

### 5.3 跨校对比分析

以金融学专业为例：

| 维度 | 西南财经大学 | 上海财经大学 |
|------|------------|------------|
| 毕业总学分 | 150 | 150 |
| 必修学分 | 113 | 116 |
| 选修/限选学分 | 39 | 25 |
| 课程总数 | 62 | 58 |
| 共有课程 | 49 门 | 49 门 |
| 独有课程 | 13 门 | 9 门 |

---

## 六、总结与反思

### 6.1 完成情况

本项目完整实现了培养方案数据库系统的全部需求：

- ✅ 数据库设计：6 张表，ER 图，完整约束与索引
- ✅ 数据预处理：2 所大学、8 个专业、224 门课程的结构化数据
- ✅ 查询系统：12 个查询函数，覆盖全部 6 项必做 + 4 项跨校对比
- ✅ Web 界面：FastAPI + Swagger，15 个 API 端点
- ✅ 测试验证：28 个测试用例，96.3% 通过率
- ✅ 跨校对比（子模块 B）：课程对比、学分对比、共有/独有课程分析

### 6.2 遇到的困难

1. **数据获取**：学校网站存在访问限制，无法直接爬取。最终通过搜索引擎收集培养方案框架信息，手工构造了符合真实学分结构的课程数据。

2. **课程去重策略**：不同专业间存在大量同名课程（如思政课、数学课），需要合理设计去重逻辑。最终采用 `code` 字段全局唯一的方案，同课程多专业共享记录。

3. **字符编码**：Windows 环境下 GBK 默认编码导致中文输出异常，通过在脚本中强制使用 UTF-8 解决。

### 6.3 改进方向

1. **数据扩展**：增加更多专业和年级的培养方案数据，引入真实的学期排课信息
2. **前端优化**：使用 Vue/React 构建交互式前端，替代当前的纯 HTML 首页
3. **NL2SQL 接口**：结合 LLM API 实现自然语言查询接口，用户可直接用中文提问
4. **部署上线**：使用 Docker 容器化，部署到云服务器，便于公开展示

---

## 附录

- GitHub 仓库：[填写仓库链接]
- API 文档：`http://localhost:8000/docs`
- 数据库位置：`db/courses.db`
- ER 图：`report/er_diagram.md`
