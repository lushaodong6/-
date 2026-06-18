"""测试 NL 正则匹配"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from app.nl2sql import match_intent, execute_intent

tests = [
    ('哪些专业开设了计量经济学', 'course_majors'),
    ('搜索包含金融的课程', 'global_search'),
    ('比较西财和上财会计学的学分要求', 'compare_credits'),
    ('法学专业的必修课有哪些', 'major_courses'),
    ('金融学有哪些必修课', 'major_courses'),
    ('高等数学多少学分', 'course_search'),
    ('金融学专业毕业需要多少学分', 'major_credits'),
    ('两校经济学共有的课程有哪些', 'compare_common'),
    ('西南财经大学金融学独有的课程', 'compare_unique'),
    ('经济学有哪些限选课程', 'major_courses'),
]

for q, expected in tests:
    intent = match_intent(q)
    if intent:
        result = execute_intent(intent)
        ok = 'OK' if intent['handler'] == expected else 'WRONG'
        print(f'[{ok}] {q}')
        print(f'      handler={intent["handler"]} (expected={expected})')
        print(f'      → {result["query_desc"][:60]} ({result["result_count"]} results)')
    else:
        print(f'[FAIL] {q} — no match')
