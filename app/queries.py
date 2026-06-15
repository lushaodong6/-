"""
查询系统 - 实现所有业务查询
"""
from app.database import query_all, query_one


# ============================================================
# 查询1：查询某专业的必修课列表
# ============================================================
def get_required_courses(major_name: str):
    """查询指定专业的必修课列表，返回课程名、学分、学时、开课学期"""
    return query_all("""
        SELECT c.code, c.name, c.credits, c.hours,
               mc.suggested_semester, cc.name AS category
        FROM major m
        JOIN major_course mc ON m.id = mc.major_id
        JOIN course c ON mc.course_id = c.id
        LEFT JOIN course_category cc ON c.category_id = cc.id
        WHERE m.name = ? AND mc.requirement_type = '必修'
        ORDER BY mc.suggested_semester, c.name
    """, (major_name,))


# ============================================================
# 查询2：查询某门课程的学分、学时信息
# ============================================================
def search_course(keyword: str):
    """模糊搜索课程，返回课程代码、名称、学分、学时、类别"""
    return query_all("""
        SELECT c.code, c.name, c.credits, c.hours, cc.name AS category
        FROM course c
        LEFT JOIN course_category cc ON c.category_id = cc.id
        WHERE c.name LIKE ?
        ORDER BY c.name
    """, (f"%{keyword}%",))


# ============================================================
# 查询3：查询某专业的总学分要求
# ============================================================
def get_total_credits(major_name: str):
    """查询某专业的总学分要求（分必修和选修统计）"""
    result = query_one("""
        SELECT m.name, m.total_credits AS required_total,
               SUM(CASE WHEN mc.requirement_type = '必修' THEN c.credits ELSE 0 END) AS required_credits,
               SUM(CASE WHEN mc.requirement_type = '限选' THEN c.credits ELSE 0 END) AS limited_elective_credits,
               SUM(CASE WHEN mc.requirement_type = '选修' THEN c.credits ELSE 0 END) AS elective_credits,
               SUM(c.credits) AS all_credits
        FROM major m
        JOIN major_course mc ON m.id = mc.major_id
        JOIN course c ON mc.course_id = c.id
        WHERE m.name = ?
        GROUP BY m.id
    """, (major_name,))
    return result


# ============================================================
# 查询4：查询开设某门课程的所有专业
# ============================================================
def get_majors_by_course(keyword: str):
    """查询开设某门课程（模糊匹配）的所有专业及大学"""
    return query_all("""
        SELECT DISTINCT m.name AS major_name, s.name AS school_name,
               u.name AS university_name, mc.requirement_type
        FROM course c
        JOIN major_course mc ON c.id = mc.course_id
        JOIN major m ON mc.major_id = m.id
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        WHERE c.name LIKE ?
        ORDER BY u.name, m.name
    """, (f"%{keyword}%",))


# ============================================================
# 查询5：查询某学院下所有专业的培养方案概览
# ============================================================
def get_school_overview(school_name: str):
    """查询某学院下所有专业的课程数和学分统计"""
    return query_all("""
        SELECT m.name AS major_name,
               COUNT(DISTINCT mc.course_id) AS course_count,
               SUM(CASE WHEN mc.requirement_type = '必修' THEN c.credits ELSE 0 END) AS required_credits,
               SUM(CASE WHEN mc.requirement_type = '限选' THEN c.credits ELSE 0 END) AS limited_elective_credits,
               m.total_credits
        FROM major m
        JOIN school s ON m.school_id = s.id
        LEFT JOIN major_course mc ON m.id = mc.major_id
        LEFT JOIN course c ON mc.course_id = c.id
        WHERE s.name LIKE ?
        GROUP BY m.id
        ORDER BY m.name
    """, (f"%{school_name}%",))


# ============================================================
# 查询6：关键词模糊搜索课程名称
# ============================================================
def search_course_by_keyword(keyword: str, limit: int = 20):
    """全局模糊搜索课程，返回匹配的课程列表"""
    return query_all("""
        SELECT DISTINCT c.code, c.name, c.credits, c.hours, cc.name AS category,
               COUNT(DISTINCT mc.major_id) AS major_count
        FROM course c
        LEFT JOIN course_category cc ON c.category_id = cc.id
        LEFT JOIN major_course mc ON c.id = mc.course_id
        WHERE c.name LIKE ?
        GROUP BY c.id
        ORDER BY major_count DESC, c.name
        LIMIT ?
    """, (f"%{keyword}%", limit))


# ============================================================
# 子模块B：跨校对比查询
# ============================================================
def compare_major_courses(major_name: str):
    """对比两校同专业（如金融学）的课程设置"""
    return query_all("""
        SELECT u.abbreviation AS university, c.code, c.name, c.credits, c.hours,
               cc.name AS category, mc.requirement_type, mc.suggested_semester
        FROM major m
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        JOIN major_course mc ON m.id = mc.major_id
        JOIN course c ON mc.course_id = c.id
        LEFT JOIN course_category cc ON c.category_id = cc.id
        WHERE m.name LIKE ?
        ORDER BY c.name, u.abbreviation
    """, (f"%{major_name}%",))


def compare_credits_by_major(major_name: str):
    """对比两校同专业的学分要求"""
    return query_all("""
        SELECT u.abbreviation AS university, m.name AS major_name,
               m.total_credits,
               SUM(CASE WHEN mc.requirement_type = '必修' THEN c.credits ELSE 0 END) AS required_credits,
               SUM(CASE WHEN mc.requirement_type = '限选' THEN c.credits ELSE 0 END) AS limited_elective,
               COUNT(DISTINCT mc.course_id) AS course_count
        FROM major m
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        JOIN major_course mc ON m.id = mc.major_id
        JOIN course c ON mc.course_id = c.id
        WHERE m.name LIKE ?
        GROUP BY u.id, m.id
        ORDER BY u.abbreviation
    """, (f"%{major_name}%",))


def get_common_courses(major_name: str):
    """查询两校同专业共有的课程（课程名完全匹配）"""
    return query_all("""
        SELECT c.name, c.credits, c.hours,
               GROUP_CONCAT(DISTINCT u.abbreviation) AS universities
        FROM course c
        JOIN major_course mc ON c.id = mc.course_id
        JOIN major m ON mc.major_id = m.id
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        WHERE m.name LIKE ?
        GROUP BY c.name
        HAVING COUNT(DISTINCT u.id) > 1
        ORDER BY c.name
    """, (f"%{major_name}%",))


def get_unique_courses(major_name: str, university_abbr: str = "SWUFE"):
    """查询某校同专业独有的课程（对方学校没有同名课程）"""
    return query_all("""
        SELECT c.name, c.credits, c.hours, cc.name AS category, mc.requirement_type
        FROM course c
        JOIN major_course mc ON c.id = mc.course_id
        JOIN major m ON mc.major_id = m.id
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        LEFT JOIN course_category cc ON c.category_id = cc.id
        WHERE m.name LIKE ? AND u.abbreviation = ?
          AND c.name NOT IN (
              SELECT c2.name
              FROM course c2
              JOIN major_course mc2 ON c2.id = mc2.course_id
              JOIN major m2 ON mc2.major_id = m2.id
              JOIN school s2 ON m2.school_id = s2.id
              JOIN university u2 ON s2.university_id = u2.id
              WHERE m2.name LIKE ? AND u2.abbreviation != ?
              GROUP BY c2.name
          )
        ORDER BY c.name
    """, (f"%{major_name}%", university_abbr, f"%{major_name}%", university_abbr))


def list_universities():
    """列出所有大学"""
    return query_all("SELECT id, name, abbreviation FROM university ORDER BY id")


def list_schools(university_id: int = None):
    """列出所有学院（可按大学筛选）"""
    if university_id:
        return query_all("""
            SELECT s.id, s.name, u.name AS university_name
            FROM school s JOIN university u ON s.university_id = u.id
            WHERE u.id = ? ORDER BY s.name
        """, (university_id,))
    return query_all("""
        SELECT s.id, s.name, u.name AS university_name
        FROM school s JOIN university u ON s.university_id = u.id
        ORDER BY u.name, s.name
    """)


def list_majors(school_id: int = None, university_id: int = None):
    """列出所有专业（可按学院或大学筛选）"""
    sql = """
        SELECT m.id, m.name, m.degree_type, m.total_credits, m.description,
               s.name AS school_name, u.name AS university_name
        FROM major m
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        WHERE 1=1
    """
    params = []
    if school_id:
        sql += " AND s.id = ?"
        params.append(school_id)
    if university_id:
        sql += " AND u.id = ?"
        params.append(university_id)
    sql += " ORDER BY u.name, s.name, m.name"
    return query_all(sql, params)
