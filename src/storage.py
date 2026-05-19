# src/storage.py
import json
from pathlib import Path

VAULT_DIR = Path("vault")
INDEX_FILE = VAULT_DIR / "index.json"


def init_storage():
    """앱이 처음 실행될 때 폴더와 인덱스 파일을 만드는 함수"""
    VAULT_DIR.mkdir(exist_ok=True)
    if not INDEX_FILE.exists():
        _save_index([])


def save_diary(date_str, title, encrypted_content, emotion, summary, tags):
    """팀원 D(CLI)나 C(AI)가 넘겨준 데이터를 받아 JSON 파일로 저장하는 함수"""
    init_storage()
    day_dir = VAULT_DIR / date_str
    day_dir.mkdir(exist_ok=True)

    entry = {
        "date": date_str,
        "title": title,
        "content": encrypted_content,
        "emotion": emotion,
        "summary": summary,
        "tags": tags if isinstance(tags, list) else []
    }

    diary_path = day_dir / "diary.json"
    with open(diary_path, 'w', encoding='utf-8') as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)

    # 인덱스 업데이트 (같은 날짜 항목은 교체)
    index = _load_index()
    index = [e for e in index if e.get("date") != date_str]
    index.append({
        "date": date_str,
        "title": title,
        "emotion": emotion,
        "summary": summary,
        "tags": tags if isinstance(tags, list) else []
    })
    index.sort(key=lambda x: x["date"], reverse=True)
    _save_index(index)
    return entry


def load_diary(date_str):
    """지정된 날짜의 일기 데이터를 읽어서 딕셔너리로 반환하는 함수"""
    diary_path = VAULT_DIR / date_str / "diary.json"
    if not diary_path.exists():
        return None
    with open(diary_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_diaries(keyword=None, tag=None):
    """키워드나 태그로 일기를 검색해 목록을 반환하는 함수"""
    index = _load_index()
    results = []
    for entry in index:
        if tag and tag not in entry.get("tags", []):
            continue
        if keyword:
            kw = keyword.lower()
            title_match = kw in entry.get("title", "").lower()
            summary_match = kw in entry.get("summary", "").lower()
            tag_match = any(kw in t.lower() for t in entry.get("tags", []))
            if not (title_match or summary_match or tag_match):
                continue
        results.append(entry)
    return results


def _load_index():
    if not INDEX_FILE.exists():
        return []
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def _save_index(index):
    VAULT_DIR.mkdir(exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
