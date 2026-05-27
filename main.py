# src/main.py
import sys
import getpass
from datetime import datetime
from cli import parse_arguments

# [모든 팀원의 모듈 최종 통합]
from ai_analyzer import AIAnalyzer
from emotion_analytics import EmotionAnalytics
from config_manager import ConfigManager
from security import encrypt_text, decrypt_text
import storage  

def authenticate(config: ConfigManager) -> tuple[bool, str]:
    """비밀번호 인증을 진행하고 패스워드 평문을 반환합니다."""
    stored_hash = config.get("security.password_hash")
    
    # 1. 초기 실행 (비밀번호 등록)
    if not stored_hash:
        print("🔐 [초기 설정] AI 보안 일기장에 오신 것을 환영합니다!")
        print("안전한 일기장 사용을 위해 사용할 비밀번호를 설정해 주세요. (8자 이상, 특수문자 포함)")
        
        while True:
            pwd = getpass.getpass("새 비밀번호 입력: ")
            if not pwd:
                print("[오류] 비밀번호는 필수 입력 사항입니다.")
                continue
            pwd_confirm = getpass.getpass("새 비밀번호 확인: ")
            
            if pwd != pwd_confirm:
                print("❌ 비밀번호가 일치하지 않습니다. 다시 시도하세요.\n")
                continue
                
            if config.change_password(pwd):
                username = input("사용하실 닉네임을 입력하세요 (기본값: User): ").strip()
                if username:
                    config.set("user.username", username)
                print(f"🎉 설정 완료! 반갑습니다, {config.get('user.username')}님.")
                return True, pwd
            else:
                print("❌ 유효하지 않은 비밀번호 형식입니다. 다시 입력해 주세요.\n")

    # 2. 로그인
    print(f"🔒 {config.get('user.username')}님의 일기장 잠금을 해제합니다.")
    max_attempts = 3
    for attempt in range(max_attempts):
        pwd = getpass.getpass("비밀번호를 입력하세요: ")
        if config.verify_password(pwd):
            print("🔓 인증 성공! 일기장을 엽니다.\n")
            return True, pwd
        else:
            print(f"❌ 비밀번호가 틀렸습니다. (남은 횟수: {max_attempts - attempt - 1}/3)")
            
    print("\n🚨 [보안] 비밀번호 3회 오류로 프로그램을 강제 종료합니다.")
    return False, ""


def main():
    # 저장소 초기화 (vault 폴더 등이 없으면 자동 생성)
    storage.init_storage()
    
    config = ConfigManager("config.json")
    is_authenticated, password_key = authenticate(config)
    if not is_authenticated:
        sys.exit(1)

    try:
        args = parse_arguments()
        
        # ------------------------------------------------------------
        # 1) 일기 쓰기 (vault write)
        # ------------------------------------------------------------
        if args.command == "write":
            print("📝 [시스템] 새로운 일기 작성을 시작합니다.\n")
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
                tags=tags_list
            )
            print("💾 [저장 완료] 일기가 안전하게 암호화되어 저장되었습니다.")

        # ------------------------------------------------------------
        # 2) 일기 조회 (vault read --date YYYY-MM-DD)
        # ------------------------------------------------------------
        elif args.command == "read":
            print(f"🔍 [시스템] {args.date} 날짜의 일기를 조회합니다.")
            
            # [저장소 연동] 파일 읽어오기
            diary_data = storage.load_diary(args.date)
            
            if not diary_data:
                print(f"❌ {args.date}에 작성된 일기가 없습니다.")
                return
                
            print("\n🔓 [보안] 일기장을 복호화하는 중...")
            try:
                # [보안 연동] 읽어온 암호문을 복호화해서 평문으로 변환
                decrypted_content = decrypt_text(diary_data["content"], password_key)
                
                print("\n" + "="*20 + f" 📅 {diary_data['date']} 일기 " + "="*20)
                print(f"💜 오늘의 감정: {diary_data['emotion']}")
                print(f"🏷️ 태그: {', '.join(diary_data['tags'])}")
                print("-" * 50)
                print(decrypted_content)
                print("=" * 54 + "\n")
            except ValueError as e:
                print(f"❌ 복호화 실패: {e}")

        # ------------------------------------------------------------
        # 3) 일기 검색 (vault search --tag 태그)
        # ------------------------------------------------------------
        elif args.command == "search":
            print(f"🔎 [시스템] '{args.tag}' 태그가 포함된 일기를 검색합니다.\n")
            
            # [저장소 연동] 태그 검색 수행
            search_results = storage.search_diaries(tag=args.tag)
            
            if not search_results:
                print(f"📭 '{args.tag}' 태그를 가진 일기가 없습니다.")
                return
                
            print(f"✨ 총 {len(search_results)}개의 일기를 찾았습니다:")
            print("-" * 60)
            for entry in search_results:
                print(f"📅 날짜: {entry['date']} | 💜 감정: {entry['emotion']}")
                print(f"📌 요약: {entry['summary']}")
                print(f"🏷️ 태그: {', '.join(entry['tags'])}")
                print("-" * 60)

        # ------------------------------------------------------------
        # 4) 감정 통계 시각화 (vault stats [--days N])
        # ------------------------------------------------------------
        elif args.command == "stats":
            print(f"📊 [시스템] 최근 {args.days}일간의 감정 통계를 출력합니다.")
            analytics = EmotionAnalytics()
            print(analytics.display_summary(days=args.days))
            
            chart_type = config.get("display.chart_type", "ascii")
            if chart_type == "matplotlib":
                try:
                    fig = analytics.plot_matplotlib_chart(days=args.days, show=False)
                    if fig:
                        import matplotlib.pyplot as plt
                        plt.savefig("emotion_chart.png", dpi=100, bbox_inches='tight')
                        plt.close()
                        print("💾 [시각화] 'emotion_chart.png' 파일로 그래프가 저장되었습니다!")
                except Exception:
                    print(analytics.plot_ascii_bar_chart(days=args.days))
            else:
                print(analytics.plot_ascii_bar_chart(days=args.days))

    except Exception as e:
        print(f"[오류] 예기치 못한 에러가 발생했습니다: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
