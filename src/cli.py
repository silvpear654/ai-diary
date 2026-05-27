# src/cli.py
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="AI 보안 일기장 - CLI 컨트롤러")
    subparsers = parser.add_subparsers(dest="command", required=True, help="사용할 명령어를 선택하세요.")

    # 1. vault write
    subparsers.add_parser("write", help="새로운 일기를 작성합니다.")

    # 2. vault read --date YYYY-MM-DD
    read_parser = subparsers.add_parser("read", help="일기를 읽어옵니다.")
    read_parser.add_argument("--date", required=True, help="조회할 날짜 (YYYY-MM-DD)")

    # 3. vault search --tag 태그
    search_parser = subparsers.add_parser("search", help="일기를 검색합니다.")
    search_parser.add_argument("--tag", required=True, help="검색할 태그")

    # ------ [추가: vault stats --days 7] ------
    # 감정 통계를 시각화하여 보여주는 명령어입니다.
    stats_parser = subparsers.add_parser("stats", help="최근 감정 통계 및 그래프를 확인합니다.")
    stats_parser.add_argument(
        "--days", 
        type=int, 
        default=7, 
        help="조회할 기간 (기본값: 7일)"
    )

    return parser.parse_args()
