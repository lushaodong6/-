"""
基于官方PDF数据重建数据库
"""
import json, sqlite3, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "db", "courses.db")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "db", "schema.sql")

# 课程类别映射
CATEGORY_MAP = {
    "思想政治理论课": 1, "数学类": 2, "数学类（A类）": 2, "数学类（B类）": 2,
    "数学类（C类）": 2, "外语类": 3, "人工智能通识": 4, "体育类": 5,
    "综合素质": 6, "通识核心": 7, "通识选修": 8,
    "学科基础课": 9, "大类平台课": 10, "专业核心课": 11,
    "专业选修课": 12, "跨专业选修": 13, "实验与实践": 14,
}

def init_db(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

def load_json(filename):
    with open(os.path.join(PROJECT_ROOT, "data", "raw", filename), "r", encoding="utf-8") as f:
        return json.load(f)

def insert_metadata(conn):
    cur = conn.cursor()
    # 大学
    cur.execute("INSERT OR IGNORE INTO university VALUES (1,'西南财经大学','SWUFE')")
    cur.execute("INSERT OR IGNORE INTO university VALUES (2,'上海财经大学','SUFE')")
    # 类别
    for name, cid in CATEGORY_MAP.items():
        cur.execute("INSERT OR IGNORE INTO course_category (id,name) VALUES (?,?)", (cid, name))
    conn.commit()

def process_swufe(conn):
    """处理西南财经大学v2格式数据"""
    cur = conn.cursor()
    data = load_json("courses_swufe_v2.json")

    school_id = 0
    major_id = 0
    course_codes = {}
    total_links = 0

    for sname, sdata in data["schools"].items():
        school_id += 1
        cur.execute("INSERT OR IGNORE INTO school (id,name,university_id) VALUES (?,?,?)",
                   (school_id, sname, 1))

        for mname, mdata in sdata["majors"].items():
            major_id += 1
            cur.execute("""INSERT OR REPLACE INTO major (id,name,school_id,degree_type,total_credits)
                         VALUES (?,?,?,?,?)""",
                       (major_id, mname, school_id, mdata.get("degree","本科"), mdata["total_credits"]))

            for req_type in ["必修", "选修"]:
                for c in mdata["courses"].get(req_type, []):
                    code, name, credits, hours, cat_name, sem = c

                    # 插入课程（去重）
                    cat_id = CATEGORY_MAP.get(cat_name, 14)
                    if code not in course_codes:
                        cur.execute("""INSERT OR IGNORE INTO course (code,name,credits,hours,category_id)
                                     VALUES (?,?,?,?,?)""",
                                   (code, name, credits, hours, cat_id))
                        course_codes[code] = cur.lastrowid or \
                            cur.execute("SELECT id FROM course WHERE code=?", (code,)).fetchone()[0]

                    cid = course_codes[code]
                    # 插入关联
                    cur.execute("""INSERT OR REPLACE INTO major_course
                                 (major_id,course_id,requirement_type,suggested_semester)
                                 VALUES (?,?,?,?)""",
                               (major_id, cid, req_type, sem))
                    total_links += 1

    conn.commit()
    print(f"SWUFE: {school_id} schools, {major_id} majors, {len(course_codes)} courses, {total_links} links")

def process_sufe(conn):
    """处理上海财经大学数据"""
    cur = conn.cursor()
    data = load_json("courses_sufe.json")

    # SUFE schools start from SWUFE count + 1
    school_id_offset = 5  # SWUFE has 5 schools
    major_id_offset = 8   # SWUFE has 8 majors

    for i, (mname, mdata) in enumerate(data["majors"].items()):
        major_id = mdata["major_id"]
        school_name_map = {
            6: "金融学院", 7: "经济学院", 8: "会计学院"
        }
        sname = school_name_map.get(major_id, "未知学院")
        school_id = major_id - 3  # 6,7,8 -> 3,4,5 offset within SUFE

        cur.execute("INSERT OR IGNORE INTO school (id,name,university_id) VALUES (?,?,?)",
                   (school_id_offset + school_id - 2, sname, 2))
        cur.execute("INSERT OR REPLACE INTO major (id,name,school_id,degree_type,total_credits) VALUES (?,?,?,?,?)",
                   (major_id, mname, school_id_offset + school_id - 2, "本科", 150))

        for c in mdata["courses"]:
            code, name, credits, hours = c["code"], c["name"], c["credits"], c["hours"]
            cat_id = c["category_id"]
            req = c["requirement_type"]
            sem = c["semester"]

            cur.execute("INSERT OR IGNORE INTO course (code,name,credits,hours,category_id) VALUES (?,?,?,?,?)",
                       (code, name, credits, hours, cat_id))
            cid = cur.execute("SELECT id FROM course WHERE code=?", (code,)).fetchone()[0]
            cur.execute("""INSERT OR REPLACE INTO major_course
                         (major_id,course_id,requirement_type,suggested_semester) VALUES (?,?,?,?)""",
                       (major_id, cid, req, sem))

    conn.commit()
    print(f"SUFE data imported")

def main():
    # 删除旧数据库
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    init_db(conn)
    insert_metadata(conn)
    process_swufe(conn)
    process_sufe(conn)

    # 统计
    cur = conn.cursor()
    print("\n===== 数据库统计 =====")
    for t in ["university","school","major","course","course_category","major_course"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n}")

    print("\n===== 各专业学分 =====")
    for row in cur.execute("""
        SELECT u.abbreviation, s.name, m.name, m.total_credits
        FROM major m JOIN school s ON m.school_id=s.id JOIN university u ON s.university_id=u.id
        ORDER BY u.id, s.name, m.name
    """):
        print(f"  [{row[0]}] {row[1]} > {row[2]} ({row[3]}学分)")

    conn.close()
    print(f"\nDone! DB: {DB_PATH}")

if __name__ == "__main__":
    main()
