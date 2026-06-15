"""
数据预处理脚本
从 raw/ 目录读取原始 JSON 数据，清洗后输出到 processed/
目前原始数据已经是结构化 JSON，本脚本主要做数据校验和统计。
"""
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def validate_course_data(data, source_name):
    """校验课程数据完整性"""
    issues = []
    for major_name, major_data in data["majors"].items():
        major_id = major_data["major_id"]
        courses = major_data["courses"]

        # 检查课程数量
        if len(courses) < 20:
            issues.append(f"  [!] {major_name}: 课程数过少 ({len(courses)})")

        # 检查必修课学分
        required_credits = sum(
            c["credits"] for c in courses if c["requirement_type"] == "必修"
        )
        elective_credits = sum(
            c["credits"] for c in courses if c["requirement_type"] != "必修"
        )

        print(f"  [{source_name}] {major_name} (ID={major_id}): "
              f"{len(courses)} 门课程, 必修 {required_credits:.1f} 学分, "
              f"选修/限选 {elective_credits:.1f} 学分, "
              f"合计 {required_credits + elective_credits:.1f} 学分")

    return issues


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("=== 数据预处理与校验 ===\n")

    all_issues = []

    for filename in ["courses_swufe.json", "courses_sufe.json"]:
        filepath = os.path.join(RAW_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"校验 {filename}:")
        issues = validate_course_data(data, filename.replace(".json", ""))
        all_issues.extend(issues)

        # 输出处理后的数据（同结构，但验证通过）
        out_path = os.path.join(PROCESSED_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  -> 已保存到 {out_path}\n")

    # 输出统计汇总
    print("=" * 40)
    if all_issues:
        print("发现以下问题:")
        for i in all_issues:
            print(i)
    else:
        print("所有数据校验通过！")


if __name__ == "__main__":
    main()
