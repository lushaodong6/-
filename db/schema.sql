-- ============================================
-- 培养方案数据库系统 - 建表语句
-- ============================================

-- 大学表
CREATE TABLE IF NOT EXISTS university (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    abbreviation TEXT NOT NULL UNIQUE
);

-- 学院表
CREATE TABLE IF NOT EXISTS school (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    university_id INTEGER NOT NULL,
    FOREIGN KEY (university_id) REFERENCES university(id),
    UNIQUE(name, university_id)
);

-- 专业表
CREATE TABLE IF NOT EXISTS major (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    school_id INTEGER NOT NULL,
    degree_type TEXT NOT NULL DEFAULT '本科',
    total_credits REAL,
    description TEXT,
    FOREIGN KEY (school_id) REFERENCES school(id),
    UNIQUE(name, school_id)
);

-- 课程类别表
CREATE TABLE IF NOT EXISTS course_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- 课程表（去重：同一门课只存一条，跨专业共享）
CREATE TABLE IF NOT EXISTS course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    credits REAL NOT NULL,
    hours REAL NOT NULL,
    category_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES course_category(id)
);

-- 专业-课程关联表（多对多）
CREATE TABLE IF NOT EXISTS major_course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    requirement_type TEXT NOT NULL CHECK(requirement_type IN ('必修', '限选', '选修')),
    suggested_semester INTEGER CHECK(suggested_semester BETWEEN 1 AND 8),
    FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    UNIQUE(major_id, course_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_major_school ON major(school_id);
CREATE INDEX IF NOT EXISTS idx_course_category ON course(category_id);
CREATE INDEX IF NOT EXISTS idx_major_course_major ON major_course(major_id);
CREATE INDEX IF NOT EXISTS idx_major_course_course ON major_course(course_id);
CREATE INDEX IF NOT EXISTS idx_course_name ON course(name);
CREATE INDEX IF NOT EXISTS idx_major_course_requirement ON major_course(requirement_type);
