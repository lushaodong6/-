"""
培养方案数据库 - 数据导入脚本
读取 raw/ 目录下的 JSON 数据文件，导入 SQLite 数据库
"""
import json
import sqlite3
import os
import sys

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "db", "courses.db")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "db", "schema.sql")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")


def load_json(filename):
    """加载 JSON 文件"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_db(conn):
    """执行建表 SQL"""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    print("[OK] 数据库表创建完成")


def import_metadata(conn, metadata):
    """导入大学、学院、专业、课程类别元数据"""
    cur = conn.cursor()

    # 大学
    for u in metadata["universities"]:
        cur.execute(
            "INSERT OR IGNORE INTO university (id, name, abbreviation) VALUES (?, ?, ?)",
            (u["id"], u["name"], u["abbreviation"]),
        )

    # 学院
    for s in metadata["schools"]:
        cur.execute(
            "INSERT OR IGNORE INTO school (id, name, university_id) VALUES (?, ?, ?)",
            (s["id"], s["name"], s["university_id"]),
        )

    # 专业
    for m in metadata["majors"]:
        cur.execute(
            "INSERT OR IGNORE INTO major (id, name, school_id, degree_type, total_credits, description) VALUES (?, ?, ?, ?, ?, ?)",
            (m["id"], m["name"], m["school_id"], m["degree_type"], m["total_credits"], m["description"]),
        )

    # 课程类别
    for c in metadata["course_categories"]:
        cur.execute(
            "INSERT OR IGNORE INTO course_category (id, name, description) VALUES (?, ?, ?)",
            (c["id"], c["name"], c["description"]),
        )

    conn.commit()
    print(f"[OK] 元数据导入完成: {len(metadata['universities'])} 所大学, "
          f"{len(metadata['schools'])} 个学院, {len(metadata['majors'])} 个专业, "
          f"{len(metadata['course_categories'])} 个课程类别")


def import_courses(conn, data):
    """导入课程数据和专业-课程关联"""
    cur = conn.cursor()

    total_courses = 0
    total_links = 0

    for major_name, major_data in data["majors"].items():
        major_id = major_data["major_id"]
        courses = major_data["courses"]

        for c in courses:
            # 插入课程（去重，按 code 唯一）
            cur.execute(
                """INSERT OR IGNORE INTO course (code, name, credits, hours, category_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (c["code"], c["name"], c["credits"], c["hours"], c["category_id"]),
            )

            # 获取课程 id（新插入的或已存在的）
            cur.execute("SELECT id FROM course WHERE code = ?", (c["code"],))
            course_id = cur.fetchone()[0]

            # 插入专业-课程关联
            cur.execute(
                """INSERT OR REPLACE INTO major_course
                   (major_id, course_id, requirement_type, suggested_semester)
                   VALUES (?, ?, ?, ?)""",
                (major_id, course_id, c["requirement_type"], c["semester"]),
            )
            total_links += 1

        total_courses = cur.execute("SELECT COUNT(*) FROM course").fetchone()[0]

    conn.commit()
    print(f"[OK] 课程导入完成: {total_courses} 门去重课程, {total_links} 条关联记录")


def validate(conn):
    """数据验证"""
    cur = conn.cursor()

    # 统计各表行数
    tables = ["university", "school", "major", "course", "course_category", "major_course"]
    print("\n========== 数据统计 ==========")
    for t in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count} 行")

    # 各专业学分汇总
    print("\n========== 各专业学分汇总 ==========")
    rows = cur.execute("""
        SELECT u.abbreviation, s.name AS school, m.name AS major, m.total_credits,
               SUM(c.credits) AS actual_total
        FROM major m
        JOIN school s ON m.school_id = s.id
        JOIN university u ON s.university_id = u.id
        JOIN major_course mc ON m.id = mc.major_id
        JOIN course c ON mc.course_id = c.id
        WHERE mc.requirement_type = '必修'
        GROUP BY m.id
        ORDER BY u.abbreviation, m.name
    """).fetchall()

    for r in rows:
        print(f"  [{r[0]}] {r[1]} > {r[2]}: 理论 {r[3]} 学分, 必修课累计 {r[4]:.1f} 学分")

    # 检查数据完整性
    print("\n========== 数据完整性检查 ==========")
    orphan_courses = cur.execute("""
        SELECT COUNT(*) FROM course c
        WHERE NOT EXISTS (SELECT 1 FROM major_course mc WHERE mc.course_id = c.id)
    """).fetchone()[0]
    print(f"  无关联的课程: {orphan_courses}")

    orphan_links = cur.execute("""
        SELECT COUNT(*) FROM major_course mc
        WHERE NOT EXISTS (SELECT 1 FROM major m WHERE m.id = mc.major_id)
           OR NOT EXISTS (SELECT 1 FROM course c WHERE c.id = mc.course_id)
    """).fetchone()[0]
    print(f"  无效关联: {orphan_links}")


def main():
    print("=== 培养方案数据库导入工具 ===\n")

    # 加载数据
    print("[1/4] 加载数据文件...")
    metadata = load_json("metadata.json")
    swufe = load_json("courses_swufe.json")
    sufe = load_json("courses_sufe.json")
    print(f"  metadata.json: {len(metadata['majors'])} 个专业元数据")
    print(f"  courses_swufe.json: {len(swufe['majors'])} 个专业课程")
    print(f"  courses_sufe.json: {len(sufe['majors'])} 个专业课程")

    # 连接数据库
    print(f"\n[2/4] 连接数据库 {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 建表
    print("\n[3/4] 创建数据库表...")
    init_db(conn)

    # 导入数据
    print("\n[4/4] 导入数据...")
    import_metadata(conn, metadata)
    import_courses(conn, swufe)
    import_courses(conn, sufe)

    # 验证
    validate(conn)

    conn.close()
    print(f"\n=== 导入完成！数据库位置: {DB_PATH} ===")


if __name__ == "__main__":
    main()
