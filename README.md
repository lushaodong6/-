# 培养方案数据库系统

数据库课程作业 —— 题目三：培养方案数据库系统

## 功能简介

构建西南财经大学及上海财经大学培养方案的数据库系统，支持：
- 查询某专业的必修课列表
- 查询课程的学分、学时信息
- 查询专业总学分要求
- 查询开设某门课程的所有专业
- 查询学院下所有专业的培养方案概览
- 关键词模糊搜索课程
- 跨校培养方案对比（子模块 B）
- 自然语言查询接口

## 技术栈

- Python 3.13 + FastAPI + SQLite
- 数据来源：西南财经大学2025版官方培养方案PDF、上海财经大学官网培养方案

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 导入数据库
python scripts/rebuild_db.py

# 3. 启动服务
uvicorn app.main:app --reload

# 4. 打开浏览器访问
# 首页: http://localhost:8000
# 测试页: http://localhost:8000/test
# API 文档: http://localhost:8000/docs
```

## 项目结构

```
├── data/raw/              # 结构化课程数据(JSON)
├── scripts/               # 数据提取与导入脚本
├── db/                    # 数据库Schema与SQLite文件
├── app/                   # FastAPI 应用
├── tests/                 # 测试用例
└── report/                # 课程报告
```

## 作者

[你的姓名] - [你的学号]
