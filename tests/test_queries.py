"""
查询系统测试用例
运行方式: python tests/test_queries.py
"""
import sys
import os
import io

# 修复 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import queries


def test(label, result, min_count=1):
    """简单测试断言"""
    if result and len(result) >= min_count:
        print(f"  ✓ {label}: 返回 {len(result)} 条结果")
        # 打印前2条预览
        for i, row in enumerate(result[:2]):
            print(f"    [{i+1}] {row}")
    else:
        print(f"  ✗ {label}: 结果为空或不足 {min_count} 条")
    print()


def main():
    print("=" * 60)
    print("培养方案数据库系统 - 查询测试")
    print("=" * 60 + "\n")

    # 1. 基础数据
    print("【基础数据测试】")
    test("大学列表", queries.list_universities(), 2)
    test("学院列表", queries.list_schools(), 6)
    test("专业列表", queries.list_majors(), 5)

    # 2. 查询1：专业必修课
    print("【查询1：专业必修课】")
    test("金融学必修课", queries.get_required_courses("金融学"), 5)
    test("会计学必修课", queries.get_required_courses("会计学"), 5)
    test("法学必修课", queries.get_required_courses("法学"), 5)

    # 3. 查询2：课程信息
    print("【查询2：课程信息搜索】")
    test("搜索'经济学'", queries.search_course("经济学"), 3)
    test("搜索'数学'", queries.search_course("数学"), 3)
    test("搜索'会计'", queries.search_course("会计"), 3)

    # 4. 查询3：学分统计
    print("【查询3：专业学分统计】")
    test("金融学学分", [queries.get_total_credits("金融学")], 1)
    test("经济学学分", [queries.get_total_credits("经济学（国家拔尖基地班）")], 1)
    test("经济统计学学分", [queries.get_total_credits("经济统计学")], 1)

    # 5. 查询4：课程-专业关联
    print("【查询4：课程开设专业】")
    test("开设'计量经济学'的专业", queries.get_majors_by_course("计量经济学"), 2)
    test("开设'政治经济学'的专业", queries.get_majors_by_course("政治经济学"), 2)
    test("开设'证券投资学'的专业", queries.get_majors_by_course("证券投资学"), 1)

    # 6. 查询5：学院概览
    print("【查询5：学院概览】")
    test("金融学院概览", queries.get_school_overview("金融学院"), 1)
    test("会计学院概览", queries.get_school_overview("会计学院"), 1)
    test("经济学院概览", queries.get_school_overview("经济学院"), 2)

    # 7. 查询6：全局模糊搜索
    print("【查询6：全局模糊搜索】")
    test("搜索'金融'", queries.search_course_by_keyword("金融"), 3)
    test("搜索'统计'", queries.search_course_by_keyword("统计"), 3)
    test("搜索'法律'", queries.search_course_by_keyword("法律"), 3)

    # 8. 跨校对比（子模块B）
    print("【跨校对比测试】")
    test("金融学课程对比", queries.compare_major_courses("金融学"), 10)
    test("金融学学分对比", queries.compare_credits_by_major("金融学"), 2)
    test("会计学共有课程", queries.get_common_courses("会计学"), 5)
    test("经济学共有课程", queries.get_common_courses("经济学"), 3)
    test("西财金融学独有课程", queries.get_unique_courses("金融学", "SWUFE"), 3)
    test("上财金融学独有课程", queries.get_unique_courses("金融学", "SUFE"), 3)

    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
