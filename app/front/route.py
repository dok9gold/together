from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

router = APIRouter()


def mount_static(app):
    """main.py에서 호출하여 static 파일 서빙"""
    app.mount("/", StaticFiles(directory="app/front/static", html=True), name="static")
