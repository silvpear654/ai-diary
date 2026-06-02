# src/storage.py
import sys
import json
from pathlib import Path

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = PROJECT_ROOT / "vault"
INDEX_FILE = VAULT_DIR / "index.json"


def set_user_dir(user_dir: Path):
    """사용자별 vault 경로를 세션에 맞게 설정합니다."""
    global VAULT_DIR, INDEX_FILE
    VAULT_DIR = Path(user_dir) / "vault"
    INDEX_FILE = VAULT_DIR / "index.json"


def init_storage():
    """앱이 처음 실행될 때 폴더와 인덱스 파일을 만드는 함수"""
    VAULT_DIR.mkdir(exist_ok=True)
    if not INDEX_FILE.exists():
        _save_index([])


def save_diary(date_str, title, encrypted_content, emotion, summary, tags, password_key=None):
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
    index = _load_index(password_key)
    index = [e for e in index if e.get("date") != date_str]
    index.append({
        "date": date_str,
        "title": title,
        "emotion": emotion,
        "summary": summary,
        "tags": tags if isinstance(tags, list) else []
    })
    index.sort(key=lambda x: x["date"], reverse=True)
    _save_index(index, password_key)
    return entry


def load_diary(date_str):
    """지정된 날짜의 일기 데이터를 읽어서 딕셔너리로 반환하는 함수"""
    diary_path = VAULT_DIR / date_str / "diary.json"
    if not diary_path.exists():
        return None
    with open(diary_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_diaries(keyword=None, tag=None, password_key=None):
    """키워드나 태그로 일기를 검색해 목록을 반환하는 함수"""
    index = _load_index(password_key)
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


def migrate_index_to_encrypted(password_key):
    """기존 평문 인덱스 파일이 존재한다면, 이를 복호화 및 암호화 포맷으로 다시 저장합니다."""
    if not INDEX_FILE.exists():
        return
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if content and content.startswith('['):
            # 평문 JSON 인덱스로드 후 암호화하여 저장
            index = json.loads(content)
            _save_index(index, password_key)
            print("🔒 [보안] 기존 평문 인덱스를 안전하게 암호화하여 변환했습니다.")
    except Exception as e:
        print(f"⚠️ 인덱스 마이그레이션 중 오류 발생: {e}")


def _load_index(password_key=None):
    """인덱스 파일을 로드합니다 (암호화 복호화 지원)"""
    if not INDEX_FILE.exists():
        return []
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            return []
            
        # 평문 대괄호로 시작하면 아직 암호화되지 않은 평문 JSON
        if content.startswith('['):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return []
                
        # 암호화된 경우 복호화 시도
        if not password_key:
            return []
            
        from security import decrypt_text
        try:
            decrypted = decrypt_text(content, password_key)
            return json.loads(decrypted)
        except Exception:
            return []
    except Exception:
        return []


def _save_index(index, password_key=None):
    """인덱스 파일을 안전하게 저장합니다"""
    VAULT_DIR.mkdir(exist_ok=True)
    try:
        index_str = json.dumps(index, indent=2, ensure_ascii=False)
        
        if password_key:
            from security import encrypt_text
            encrypted_str = encrypt_text(index_str, password_key)
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypted_str)
        else:
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                f.write(index_str)
        return True
    except Exception as e:
        print(f"❌ 인덱스 저장 실패: {e}")
        return False
