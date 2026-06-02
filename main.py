# src/main.py
import sys
import os
import warnings
from datetime import datetime


def _getpass(prompt):
    """getpass 래퍼: TTY 없는 환경에서는 일반 input으로 대체"""
    import getpass as _gp
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return _gp.getpass(prompt)
    except (EOFError, OSError):
        print("\n[오류] 비밀번호 입력을 위해 터미널에서 실행해주세요.")
        print("       macOS: 'dist/실행하기.command' 파일을 더블클릭하세요.\n")
        sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cli import parse_arguments

# [모든 팀원의 모듈 최종 통합]
from ai_analyzer import AIAnalyzer
from analytics import EmotionAnalytics
from config_manager import ConfigManager
from security import encrypt_text, decrypt_text
import storage

def get_users_root():
    """users/ 루트 디렉토리 경로 반환 (없으면 생성)"""
    from pathlib import Path
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(os.path.abspath(__file__)).parent
    users_root = base / "users"
    users_root.mkdir(exist_ok=True)
    return users_root


def list_users(users_root):
    """users/ 아래 config.json이 있는 사용자 목록 반환"""
    from pathlib import Path
    return sorted([
        d.name for d in Path(users_root).iterdir()
        if d.is_dir() and (d / "config.json").exists()
    ])


def delete_user(users_root):
    """사용자 삭제 — 비밀번호 확인 후 디렉토리 전체 삭제"""
    import shutil
    from pathlib import Path

    users = list_users(users_root)
    if not users:
        print("❌ 삭제할 사용자가 없습니다.")
        return

    print("\n" + "=" * 20 + " 🗑️  사용자 삭제 " + "=" * 20)
    for i, name in enumerate(users, 1):
        print(f"  {i}. {name}")
    print("  0. 취소")
    print("=" * 54)

    choice = input("삭제할 사용자 번호 > ").strip()
    if choice == "0" or not choice:
        print("취소했습니다.")
        return
    if not (choice.isdigit() and 1 <= int(choice) <= len(users)):
        print("❌ 올바른 번호를 입력하세요.")
        return

    username = users[int(choice) - 1]
    user_dir = Path(users_root) / username

    # 비밀번호 확인
    print(f"\n⚠️  '{username}' 사용자와 모든 일기 데이터가 영구 삭제됩니다.")
    config = ConfigManager(str(user_dir / "config.json"))
    for attempt in range(3):
        pwd = _getpass(f"[{username}] 비밀번호를 입력하세요: ")
        if config.verify_password(pwd):
            break
        remaining = 2 - attempt
        if remaining > 0:
            print(f"❌ 비밀번호가 틀렸습니다. (남은 횟수: {remaining}/3)")
        else:
            print("❌ 비밀번호 3회 오류. 삭제를 취소합니다.")
            return
    else:
        return

    confirm = input(f"정말 삭제하시겠습니까? (삭제하려면 '{username}' 입력): ").strip()
    if confirm != username:
        print("취소했습니다.")
        return

    shutil.rmtree(user_dir)
    print(f"✅ '{username}' 사용자가 삭제되었습니다.")


def select_or_create_user(users_root):
    """사용자 선택 또는 신규 생성. (username, user_dir) 반환"""
    from pathlib import Path
    INVALID_CHARS = set('/\\:*?"<>|')

    while True:
        users = list_users(users_root)
        print("\n" + "=" * 20 + " 👤 사용자 선택 " + "=" * 20)
        if users:
            for i, name in enumerate(users, 1):
                print(f"  {i}. {name}")
        else:
            print("  (등록된 사용자가 없습니다)")
        print("  0. 새 사용자 추가")
        print("  d. 사용자 삭제")
        print("=" * 54)

        choice = input("선택 > ").strip().lower()

        if choice == "d":
            delete_user(users_root)
            continue

        if choice == "0":
            username = input("새 사용자 이름: ").strip()
            if not username:
                print("❌ 이름을 입력해주세요.")
                continue
            if any(c in INVALID_CHARS for c in username):
                print("❌ 이름에 사용할 수 없는 문자가 포함되어 있습니다 (/ \\ : * ? \" < > |)")
                continue
            user_dir = Path(users_root) / username
            if user_dir.exists():
                print(f"❌ '{username}' 사용자가 이미 존재합니다.")
                continue
            user_dir.mkdir()
            print(f"✅ 사용자 '{username}' 생성 완료!")
            return username, user_dir

        if choice.isdigit() and 1 <= int(choice) <= len(users):
            username = users[int(choice) - 1]
            return username, Path(users_root) / username

        print("❌ 올바른 번호를 입력하세요.")


def authenticate(config: ConfigManager, username: str) -> tuple[bool, str]:
    """비밀번호 인증을 진행하고 패스워드 평문을 반환합니다."""
    stored_hash = config.get("security.password_hash")

    # 1. 신규 사용자 — 비밀번호 등록
    if not stored_hash:
        print(f"🔐 [{username}] 처음 사용하시는군요! 비밀번호를 설정해주세요. (8자 이상, 문자/숫자/특수문자 포함)")
        while True:
            pwd = _getpass("새 비밀번호 입력: ")
            if not pwd:
                print("[오류] 비밀번호는 필수입니다.")
                continue
            pwd_confirm = _getpass("새 비밀번호 확인: ")
            if pwd != pwd_confirm:
                print("❌ 비밀번호가 일치하지 않습니다. 다시 시도하세요.\n")
                continue
            if config.change_password(pwd):
                config.set("user.username", username)
                print(f"🎉 설정 완료! 반갑습니다, {username}님.")
                return True, pwd
            else:
                print()
                continue

    # 2. 기존 사용자 — 로그인
    print(f"🔒 {username}님의 일기장 잠금을 해제합니다.")
    for attempt in range(3):
        pwd = _getpass("비밀번호를 입력하세요: ")
        if config.verify_password(pwd):
            print("🔓 인증 성공! 일기장을 엽니다.\n")
            return True, pwd
        print(f"❌ 비밀번호가 틀렸습니다. (남은 횟수: {2 - attempt}/3)")

    print("\n🚨 [보안] 비밀번호 3회 오류로 프로그램을 강제 종료합니다.")
    return False, ""


def interactive_write(password_key: str):
    """대화형 일기 쓰기 로직"""
    print("\n📝 [시스템] 새로운 일기 작성을 시작합니다.\n")
    print("오늘 하루는 어땠나요? 일기를 작성하고 엔터(Enter)를 눌러주세요:")
    diary_content = input("> ")
    
    if not diary_content.strip():
        print("[오류] 일기 내용이 비어있어 작성을 취소합니다.")
        return

    print("\n🤖 [시스템] AI 분석 에이전트를 가동합니다...")
    analyzer = AIAnalyzer()
    analysis_result = analyzer.analyze(diary_content)
    
    if "error" in analysis_result:
        print(f"⚠️ [분석 실패] {analysis_result['error']}")
        return

    # AI 분석 결과 출력
    print("\n" + "="*15 + " ✨ AI 일기 분석 결과 ✨ " + "="*15)
    emotion_str = analysis_result.get("emotion", "보통")
    summary_str = analysis_result.get("summary", "")
    tags_list = analysis_result.get("tags", [])
    
    print(f"💜 오늘 나의 감정 : {emotion_str}")
    print(f"📌 한 줄 요약    : {summary_str}")
    print(f"🏷️ 생성된 태그   : {', '.join(tags_list)}")
    print(f"💌 AI의 따뜻한 한마디: {analysis_result.get('feedback')}")
    print("=" * 54 + "\n")
    
    # [보안 연동] 일기 원문 암호화
    print("🔒 [보안] 일기 본문을 AES-256으로 암호화합니다.")
    encrypted_diary = encrypt_text(diary_content, password_key)

    # [저장소 연동] 암호화된 본문과 AI 분석 결과를 파일로 저장!
    today_str = datetime.now().strftime("%Y-%m-%d")
    storage.save_diary(
        date_str=today_str,
        title=f"{today_str}의 일기",
        encrypted_content=encrypted_diary, 
        emotion=emotion_str,
        summary=summary_str,
        tags=tags_list,
        password_key=password_key
    )
    print("💾 [저장 완료] 일기가 안전하게 암호화되어 저장되었습니다.")


def interactive_read(password_key: str):
    """대화형 일기 조회 로직"""
    print("\n🔍 [일기 조회] 조회할 날짜를 입력하세요 (형식: YYYY-MM-DD):")
    date_str = input("> ").strip()
    if not date_str:
        print("[오류] 날짜는 필수 입력 사항입니다.")
        return
        
    _cli_read(date_str, password_key)


def _cli_read(date_str: str, password_key: str):
    """일기 조회 처리 헬퍼"""
    print(f"🔍 [시스템] {date_str} 날짜의 일기를 조회합니다.")
    diary_data = storage.load_diary(date_str)
    
    if not diary_data:
        print(f"❌ {date_str}에 작성된 일기가 없습니다.")
        return
        
    print("\n🔓 [보안] 일기장을 복호화하는 중...")
    try:
        decrypted_content = decrypt_text(diary_data["content"], password_key)
        
        print("\n" + "="*20 + f" 📅 {diary_data['date']} 일기 " + "="*20)
        print(f"💜 오늘의 감정: {diary_data['emotion']}")
        print(f"🏷️ 태그: {', '.join(diary_data['tags'])}")
        print("-" * 50)
        print(decrypted_content)
        print("=" * 54 + "\n")
    except ValueError as e:
        print(f"❌ 복호화 실패: {e}")


def interactive_search(password_key: str):
    """대화형 일기 검색 로직"""
    print("\n🔎 [일기 검색] 검색할 태그를 입력하세요:")
    tag_str = input("> ").strip()
    if not tag_str:
        print("[오류] 태그명은 필수 입력 사항입니다.")
        return
        
    _cli_search(tag_str, password_key)


def _cli_search(tag_str: str, password_key: str):
    """일기 검색 처리 헬퍼"""
    print(f"🔎 [시스템] '{tag_str}' 태그가 포함된 일기를 검색합니다.\n")
    search_results = storage.search_diaries(tag=tag_str, password_key=password_key)
    
    if not search_results:
        print(f"📭 '{tag_str}' 태그를 가진 일기가 없습니다.")
        return
        
    print(f"✨ 총 {len(search_results)}개의 일기를 찾았습니다:")
    print("-" * 60)
    for entry in search_results:
        print(f"📅 날짜: {entry['date']} | 💜 감정: {entry['emotion']}")
        print(f"📌 요약: {entry['summary']}")
        print(f"🏷️ 태그: {', '.join(entry['tags'])}")
        print("-" * 60)


def interactive_stats(config: ConfigManager, password_key: str):
    """대화형 감정 통계 로직"""
    print("\n📊 [감정 통계] 최근 몇 일간의 통계를 보시겠습니까? (기본값: 7일):")
    days_str = input("> ").strip()
    days = 7
    if days_str:
        try:
            days = int(days_str)
        except ValueError:
            print("⚠️ 올바른 숫자가 아닙니다. 기본값 7일로 조회합니다.")
            
    _cli_stats(days, config, password_key)


def _cli_stats(days: int, config: ConfigManager, password_key: str):
    """감정 통계 처리 헬퍼"""
    print(f"📊 [시스템] 최근 {days}일간의 감정 통계를 출력합니다.")
    analytics = EmotionAnalytics(password_key=password_key)
    print(analytics.display_summary(days=days))
    
    chart_type = config.get("display.chart_type", "ascii")
    if chart_type == "matplotlib":
        try:
            fig = analytics.plot_matplotlib_chart(days=days, show=False)
            if fig:
                import matplotlib.pyplot as plt
                plt.savefig("emotion_chart.png", dpi=100, bbox_inches='tight')
                plt.close()
                print("💾 [시각화] 'emotion_chart.png' 파일로 그래프가 저장되었습니다!")
        except Exception as e:
            print(f"⚠️ [시각화 경고] matplotlib 차트 생성에 실패했습니다: {e}")
    
    print("\n📈 [시각화] 감정 꺾은선 추이:")
    print(analytics.plot_ascii_chart(days=days))
    print("\n📊 [시각화] 감정 막대 분포:")
    print(analytics.plot_ascii_bar_chart(days=days))


def run_interactive_menu(config: ConfigManager, password_key: str):
    """대화형 메뉴 루프"""
    print(f"✨ {config.get('user.username')}님, AI 보안 일기장의 메뉴 모드를 시작합니다.")
    
    while True:
        print("\n" + "="*15 + " 📂 AI 보안 일기장 메뉴 " + "="*15)
        print("1. 📝 새 일기 쓰기 (write)")
        print("2. 🔍 날짜별 일기 조회 (read)")
        print("3. 🔎 태그로 일기 검색 (search)")
        print("4. 📊 감정 분석 및 통계 보기 (stats)")
        print("5. 🚪 프로그램 종료 (exit)")
        print("=" * 49)
        
        choice = input("선택 > ").strip().lower()
        if choice in ["5", "exit", "quit", "q"]:
            print("👋 일기장을 안전하게 닫습니다. 안녕히 가세요!")
            break
            
        elif choice in ["1", "write"]:
            interactive_write(password_key)
            
        elif choice in ["2", "read"]:
            interactive_read(password_key)
            
        elif choice in ["3", "search"]:
            interactive_search(password_key)
            
        elif choice in ["4", "stats"]:
            interactive_stats(config, password_key)
            
        else:
            print("❌ 올바른 메뉴 번호(1-5) 또는 명령어를 선택해주세요.")


def execute_command(args, config: ConfigManager, password_key: str):
    """CLI 모드 실행 분기"""
    if args.command == "write":
        interactive_write(password_key)
    elif args.command == "read":
        _cli_read(args.date, password_key)
    elif args.command == "search":
        _cli_search(args.tag, password_key)
    elif args.command == "stats":
        _cli_stats(args.days, config, password_key)


def main():
    # 1. 인자 개수 분기
    is_interactive = len(sys.argv) == 1

    # 2. 도움말 옵션 체크 (로그인 없이 즉시 도움말 노출)
    if "-h" in sys.argv or "--help" in sys.argv:
        try:
            parse_arguments()
        except SystemExit:
            sys.exit(0)

    # 3. CLI 서브커맨드가 들어온 경우 -> 로그인 전 인자 선검증
    args = None
    if not is_interactive:
        try:
            args = parse_arguments()
        except SystemExit:
            sys.exit(0)

    # 4. 사용자 선택
    users_root = get_users_root()
    username, user_dir = select_or_create_user(users_root)

    # 5. 사용자별 저장소 초기화
    storage.set_user_dir(user_dir)
    storage.init_storage()

    # 6. 사용자별 설정 로드 및 인증
    config = ConfigManager(str(user_dir / "config.json"))
    is_authenticated, password_key = authenticate(config, username)
    if not is_authenticated:
        sys.exit(1)

    storage.migrate_index_to_encrypted(password_key)

    # 7. 실행 모드 실행
    if is_interactive:
        run_interactive_menu(config, password_key)
    else:
        try:
            execute_command(args, config, password_key)
        except Exception as e:
            print(f"[오류] 예기치 못한 에러가 발생했습니다: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
