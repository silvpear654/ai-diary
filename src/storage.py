# src/storage.py
import os
import json
from pathlib import Path

# 일기가 저장될 기본 폴더 경로 설정
VAULT_DIR = Path("vault")
INDEX_FILE = VAULT_DIR / "index.json"

def init_storage():
    """앱이 처음 실행될 때 폴더와 인덱스 파일을 만드는 함수"""
    pass

def save_diary(date_str, title, encrypted_content, emotion, summary, tags):
    """팀원 D(CLI)나 C(AI)가 넘겨준 데이터를 받아 JSON 파일로 저장하는 함수"""
    pass

def load_diary(date_str):
    """지정된 날짜의 일기 데이터를 읽어서 딕셔너리로 반환하는 함수"""
    pass

def search_diaries(keyword=None, tag=None):
    """키워드나 태그로 일기를 검색해 목록을 반환하는 함수"""
    pass