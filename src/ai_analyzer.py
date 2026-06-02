import sys
import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv

if getattr(sys, 'frozen', False):
    load_dotenv(Path(sys.executable).parent / '.env')
else:
    load_dotenv()



class AIAnalyzer:
    """
    사용자의 일기를 Google Gemini AI로 분석하여 감정, 요약, 키워드, 조언 등을 제공하는 클래스입니다.
    """
    # 사용 모델명. 환경 변수 GEMINI_MODEL 로 덮어쓸 수 있습니다. (기본: 2.5 flash lite)
    DEFAULT_MODEL = 'gemini-2.5-flash-lite'

    # 허용되는 감정 값 (analytics 등 다른 모듈과 약속된 5단계)
    VALID_EMOTIONS = ("매우 행복", "행복", "보통", "슬픔", "매우 슬픔")

    def __init__(self, api_key=None):
        """
        :param api_key: Gemini API 키. 입력하지 않으면 환경 변수 'GEMINI_API_KEY'에서 가져옵니다.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = None  # _setup_gemini 실패 시에도 AttributeError 방지

        if not self.api_key:
            print("⚠️ Warning: GEMINI_API_KEY가 설정되지 않았습니다. 실제 AI API 호출 대신 테스트용(Mock) 데이터가 반환됩니다.")
        else:
            self._setup_gemini()

    def _setup_gemini(self):
        """Gemini API 설정을 초기화합니다."""
        try:
            from google import genai
        except ImportError:
            print("⚠️ Error: 'google-genai' 패키지가 설치되지 않았습니다. 터미널에서 'pip install google-genai'를 실행해주세요.")
            self.api_key = None
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            # 모델명은 환경 변수로 덮어쓸 수 있으며, 없으면 기본값을 사용합니다.
            self.model = os.environ.get("GEMINI_MODEL", self.DEFAULT_MODEL)
        except Exception as e:
            # 잘못된 키 형식 등 Client 생성 단계의 오류도 안전하게 처리하여 Mock 모드로 전환합니다.
            print(f"⚠️ Error: Gemini 클라이언트 초기화에 실패했습니다 ({e}). 테스트용(Mock) 데이터로 동작합니다.")
            self.api_key = None

    def analyze(self, diary_content: str) -> dict:
        """
        일기 내용을 분석합니다.
        
        :param diary_content: 작성된 일기 텍스트
        :return: 분석 결과 (감정, 요약, 키워드 등)가 담긴 딕셔너리
        """
        if not diary_content.strip():
            return {"error": "분석할 일기 내용이 없습니다."}

        # API 키가 없거나 패키지 로드에 실패했으면 임시 데이터를 반환합니다.
        if not self.api_key:
            return self._mock_analysis(diary_content)

        return self._analyze_with_gemini(diary_content)

    def _analyze_with_gemini(self, text: str) -> dict:
        """
        Google Gemini API를 사용하여 분석하는 로직
        """
        prompt = (
            "너는 일기를 분석해주는 따뜻하고 공감 능력이 뛰어난 AI 상담사야.\n"
            "다음 일기를 읽고, 아래 JSON 형식에 맞추어 분석 결과를 한국어로 반환해줘. "
            "반드시 마크다운이나 코드 블록 없이 순수한 JSON 문자열만 응답해야 해.\n\n"
            "형식:\n"
            "{\n"
            '  "emotion": "매우 행복/행복/보통/슬픔/매우 슬픔 중 하나",\n'
            '  "summary": "일기 내용 1줄 요약",\n'
            '  "tags": ["태그1", "태그2", "태그3"],\n'
            '  "feedback": "작성자를 위한 따뜻한 조언 한마디"\n'
            "}\n\n"
            f"일기 내용:\n{text}"
        )

        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            response_text = response.text.strip()
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not match:
                return {"error": "AI 응답에서 JSON을 찾을 수 없습니다."}
            return self._normalize_result(json.loads(match.group()))
        except Exception as e:
            return {"error": f"분석 중 오류가 발생했습니다: {str(e)}"}

    def _normalize_result(self, data: dict) -> dict:
        """
        AI 응답을 약속된 스키마(emotion/summary/tags/feedback)로 보정합니다.
        키가 누락되거나 타입/값이 잘못되어도 다른 모듈이 안전하게 쓸 수 있도록 기본값을 채웁니다.
        """
        if not isinstance(data, dict):
            return {"error": "AI 응답 형식이 올바르지 않습니다."}

        emotion = data.get("emotion", "보통")
        if emotion not in self.VALID_EMOTIONS:
            emotion = "보통"

        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [str(t) for t in tags]

        return {
            "emotion": emotion,
            "summary": str(data.get("summary", "")),
            "tags": tags,
            "feedback": str(data.get("feedback", "")),
        }

    def _mock_analysis(self, _text: str) -> dict:
        """API 연동 전, 또는 테스트를 위한 임시 반환 함수"""
        return {
            "emotion": "보통",
            "summary": "[Mock] 오늘 하루는 전반적으로 평온하고 긍정적인 일이 많았습니다.",
            "tags": ["휴식", "대화", "평온"],
            "feedback": "오늘 하루도 수고 많으셨습니다. 앞으로도 이런 여유를 즐기시길 바라요!"
        }

if __name__ == "__main__":
    # .env 파일에 GEMINI_API_KEY를 설정한 후 실행하세요.
    analyzer = AIAnalyzer()
    
    sample_text = "오늘은 친구들과 오랜만에 만나서 맛있는 것도 먹고 수다도 떨었다. 시험 기간이라 스트레스가 많았는데 다 풀리는 기분이라 정말 행복했다."
    
    print("분석을 시작합니다...")
    result = analyzer.analyze(sample_text)
    
    print("\n=== 일기 분석 결과 ===")
    print(json.dumps(result, indent=4, ensure_ascii=False))