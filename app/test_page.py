"""
纯中文测试页面路由
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(HERE, "test_page.html")


def register(app: FastAPI):
    @app.get("/test", include_in_schema=False, response_class=HTMLResponse)
    def chinese_test():
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
