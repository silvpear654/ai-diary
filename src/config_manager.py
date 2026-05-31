import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import hashlib


class ConfigManager:
    """설정 파일을 관리하는 클래스"""
    
    # 기본 설정값
    DEFAULT_CONFIG = {
        "user": {
            "username": "User",
            "created_at": None
        },
        "theme": {
            "color_scheme": "dark",  # 'dark', 'light', 'custom'
            "primary_color": "#4A90E2",
            "secondary_color": "#7B68EE",
            "text_color": "#FFFFFF"
        },
        "language": "ko",  # 'ko', 'en', 'ja'
        "security": {
            "password_hash": None,
            "password_history": [],
            "last_password_change": None,
            "session_timeout": 3600  # 초 단위
        },
        "display": {
            "chart_type": "ascii",  # 'ascii', 'matplotlib'
            "chart_width": 80,
            "chart_height": 20,
            "show_grid": True
        },
        "notifications": {
            "daily_reminder": True,
            "reminder_time": "09:00"
        }
    }
    
    # 언어별 메시지
    MESSAGES = {
        "ko": {
            "config_created": "✅ 기본 설정 파일이 생성되었습니다.",
            "config_loaded": "✅ 설정이 로드되었습니다.",
            "config_saved": "✅ 설정이 저장되었습니다.",
            "invalid_theme": "❌ 유효하지 않은 테마입니다. (dark/light/custom)",
            "invalid_language": "❌ 지원하지 않는 언어입니다. (ko/en/ja)",
            "password_changed": "✅ 비밀번호가 변경되었습니다.",
            "weak_password": "❌ 약한 비밀번호입니다. 8글자 이상의 숫자, 문자, 특수문자를 포함하세요.",
        },
        "en": {
            "config_created": "✅ Default configuration file created.",
            "config_loaded": "✅ Configuration loaded.",
            "config_saved": "✅ Configuration saved.",
            "invalid_theme": "❌ Invalid theme. (dark/light/custom)",
            "invalid_language": "❌ Unsupported language. (ko/en/ja)",
            "password_changed": "✅ Password changed.",
            "weak_password": "❌ Weak password. Include numbers, letters, and special characters (8+ chars).",
        },
        "ja": {
            "config_created": "✅ デフォルト設定ファイルが作成されました。",
            "config_loaded": "✅ 設定がロードされました。",
            "config_saved": "✅ 設定が保存されました。",
            "invalid_theme": "❌ 無効なテーマです。(dark/light/custom)",
            "invalid_language": "❌ サポートされていない言語です。(ko/en/ja)",
            "password_changed": "✅ パスワードが変更されました。",
            "weak_password": "❌ 弱いパスワードです。数字、文字、特殊文字を含む8文字以上にしてください。",
        }
    }
    
    def __init__(self, config_path: str = "config.json"):
        """
        ConfigManager 초기화
        
        Args:
            config_path: 설정 파일 경로 (기본값: config.json)
        """
        path = Path(config_path)
        if not path.is_absolute():
            # config_manager.py가 속한 디렉토리의 부모 디렉토리를 루트로 삼아 절대 경로 구성
            project_root = Path(__file__).resolve().parent.parent
            self.config_path = project_root / path
        else:
            self.config_path = path
        self.config = None
        self.load_or_create()
    
    def load_or_create(self) -> Dict[str, Any]:
        """
        설정 파일을 로드하거나 없으면 기본값으로 생성
        
        Returns:
            로드된 설정 딕셔너리
        """
        if self.config_path.exists():
            self.load()
            self._print_message("config_loaded")
        else:
            self.config = self._deep_copy(self.DEFAULT_CONFIG)
            self.config["user"]["created_at"] = datetime.now().isoformat()
            self.save()
            self._print_message("config_created")
        
        return self.config
    
    def load(self) -> Dict[str, Any]:
        """설정 파일을 로드합니다"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return self.config
        except json.JSONDecodeError:
            print("⚠️ 설정 파일이 손상되었습니다. 기본값으로 초기화합니다.")
            self.config = self._deep_copy(self.DEFAULT_CONFIG)
            self.save()
            return self.config
    
    def save(self) -> bool:
        """설정을 파일에 저장합니다"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self._print_message("config_saved")
            return True
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        설정값을 가져옵니다 (점 표기법 지원)
        
        Args:
            key: 설정 키 (예: 'theme.primary_color')
            default: 키가 없을 때 반환할 기본값
        
        Returns:
            설정값
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        설정값을 변경합니다 (점 표기법 지원)
        
        Args:
            key: 설정 키 (예: 'theme.primary_color')
            value: 설정할 값
        
        Returns:
            성공 여부
        """
        keys = key.split('.')
        config = self.config
        
        # 마지막 키를 제외한 모든 키에 접근
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        return self.save()
    
    def set_theme(self, theme: str, colors: Optional[Dict[str, str]] = None) -> bool:
        """
        테마 설정
        
        Args:
            theme: 테마 ('dark', 'light', 'custom')
            colors: 커스텀 색상 (theme='custom'일 때 필수)
        
        Returns:
            성공 여부
        """
        valid_themes = ['dark', 'light', 'custom']
        if theme not in valid_themes:
            self._print_message("invalid_theme")
            return False
        
        self.config['theme']['color_scheme'] = theme
        
        if theme == 'custom' and colors:
            for color_key, color_value in colors.items():
                if color_key in self.config['theme']:
                    self.config['theme'][color_key] = color_value
        elif theme == 'dark':
            self.config['theme'].update({
                "primary_color": "#4A90E2",
                "secondary_color": "#7B68EE",
                "text_color": "#FFFFFF"
            })
        elif theme == 'light':
            self.config['theme'].update({
                "primary_color": "#2E86DE",
                "secondary_color": "#A23B72",
                "text_color": "#000000"
            })
        
        return self.save()
    
    def set_language(self, language: str) -> bool:
        """
        언어 설정
        
        Args:
            language: 언어코드 ('ko', 'en', 'ja')
        
        Returns:
            성공 여부
        """
        valid_languages = ['ko', 'en', 'ja']
        if language not in valid_languages:
            self._print_message("invalid_language")
            return False
        
        self.config['language'] = language
        return self.save()
    
    def change_password(self, new_password: str) -> bool:
        """
        비밀번호 변경
        
        Args:
            new_password: 새 비밀번호
        
        Returns:
            성공 여부
        """
        if not self._validate_password(new_password):
            self._print_message("weak_password")
            return False
        
        # 기존 비밀번호를 히스토리에 저장
        old_hash = self.config['security']['password_hash']
        if old_hash:
            if 'password_history' not in self.config['security']:
                self.config['security']['password_history'] = []
            self.config['security']['password_history'].append({
                "hash": old_hash,
                "changed_date": self.config['security']['last_password_change']
            })
        
        # 새 비밀번호 저장
        self.config['security']['password_hash'] = self._hash_password(new_password)
        self.config['security']['last_password_change'] = datetime.now().isoformat()
        
        self._print_message("password_changed")
        return self.save()
    
    def verify_password(self, password: str) -> bool:
        """
        비밀번호 검증
        
        Args:
            password: 검증할 비밀번호
        
        Returns:
            비밀번호가 일치하는지 여부
        """
        stored_hash = self.config['security']['password_hash']
        if not stored_hash:
            return False
        
        return stored_hash == self._hash_password(password)
    
    def get_password_history(self) -> list:
        """비밀번호 변경 이력 조회"""
        return self.config['security'].get('password_history', [])
    
    def display_settings(self) -> None:
        """현재 설정을 보기 좋게 출력"""
        lang = self.config.get('language', 'ko')
        
        print("\n" + "="*60)
        print("📋 현재 설정")
        print("="*60)
        print(f"👤 사용자명: {self.config['user']['username']}")
        print(f"🎨 테마: {self.config['theme']['color_scheme']}")
        print(f"🌍 언어: {self.config['language']}")
        print(f"📊 차트 유형: {self.config['display']['chart_type']}")
        print(f"⏰ 알림: {self.config['notifications']['reminder_time']}")
        print(f"🔐 마지막 비밀번호 변경: {self.config['security']['last_password_change'] or '설정되지 않음'}")
        print("="*60 + "\n")
    
    @staticmethod
    def _validate_password(password: str) -> bool:
        """
        비밀번호 유효성 검사
        - 8글자 이상
        - 숫자, 문자, 특수문자 포함
        """
        if len(password) < 8:
            return False
        
        has_digit = any(c.isdigit() for c in password)
        has_letter = any(c.isalpha() for c in password)
        has_special = any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?' for c in password)
        
        return has_digit and has_letter and has_special
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """비밀번호를 해시합니다"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _print_message(self, message_key: str) -> None:
        """설정된 언어에 따라 메시지를 출력합니다"""
        lang = self.config.get('language', 'ko') if self.config else 'ko'
        messages = self.MESSAGES.get(lang, self.MESSAGES['ko'])
        print(messages.get(message_key, message_key))
    
    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """깊은 복사를 수행합니다"""
        if isinstance(obj, dict):
            return {k: ConfigManager._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ConfigManager._deep_copy(item) for item in obj]
        else:
            return obj


# 테스트 코드
if __name__ == "__main__":
    print("🚀 ConfigManager 테스트 시작\n")
    
    # 설정 매니저 초기화
    config = ConfigManager("config.json")
    
    # 현재 설정 확인
    config.display_settings()
    
    # 언어 변경
    print("🌍 언어를 영어로 변경합니다...")
    config.set_language("en")
    print(f"현재 언어: {config.get('language')}\n")
    
    # 테마 변경
    print("🎨 테마를 light로 변경합니다...")
    config.set_theme("light")
    print(f"현재 테마: {config.get('theme.color_scheme')}\n")
    
    # 비밀번호 설정
    print("🔐 비밀번호를 설정합니다...")
    test_password = "Test@1234"
    if config.change_password(test_password):
        print(f"✅ 비밀번호 검증: {config.verify_password(test_password)}\n")
    
    # 개별 설정값 변경
    print("📊 차트 너비를 100으로 설정합니다...")
    config.set('display.chart_width', 100)
    print(f"현재 차트 너비: {config.get('display.chart_width')}\n")
    
    # 최종 설정 확인
    config.display_settings()
    
    # 설정 파일 내용 출력
    print("📄 설정 파일 내용:")
    with open("config.json", 'r', encoding='utf-8') as f:
        print(json.dumps(json.load(f), indent=2, ensure_ascii=False))
