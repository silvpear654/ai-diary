import os
import json

class AIAnalyzer:
    """
    사용자의 일기를 AI로 분석하여 감정, 요약, 키워드, 조언 등을 제공하는 클래스입니다.
    """
    def __init__(self, api_provider="openai", api_key=None):
        """
        :param api_provider: 사용할 AI 모델 ('openai', 'gemini' 등)
        :param api_key: API 키. 입력하지 않으면 환경 변수에서 가져옵니다.
        """
        self.api_provider = api_provider
        self.api_key = api_key or os.environ.get("AI_API_KEY")
        
        if not self.api_key:
            print("⚠️ Warning: API 키가 설정되지 않았습니다. 실제 AI API 호출 대신 테스트용(Mock) 데이터가 반환됩니다.")

    def analyze(self, diary_content: str) -> dict:
        """
        일기 내용을 분석합니다.
        
        :param diary_content: 작성된 일기 텍스트
        :return: 분석 결과 (감정, 요약, 키워드 등)가 담긴 딕셔너리
        """
        if not diary_content.strip():
            return {"error": "분석할 일기 내용이 없습니다."}

        # API 키가 없으면 임시 데이터를 반환합니다.
        if not self.api_key:
            return self._mock_analysis(diary_content)

        # 설정된 제공자에 맞게 분석 메서드를 호출합니다.
        if self.api_provider == "openai":
            return self._analyze_with_openai(diary_content)
        elif self.api_provider == "gemini":
            return self._analyze_with_gemini(diary_content)
        else:
            raise ValueError(f"지원하지 않는 API 제공자입니다: {self.api_provider}")

    def _analyze_with_openai(self, text: str) -> dict:
        """
        OpenAI API를 사용하여 분석하는 로직
        (사전 준비: pip install openai)
        """
        # import openai
        # client = openai.OpenAI(api_key=self.api_key)
        # response = client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": "너는 일기를 분석해주는 따뜻한 AI 상담사야. 일기를 보고 감정(긍정/부정/중립), 1줄 요약, 핵심 키워드 3개, 따뜻한 조언 한마디를 JSON 형태로 반환해줘."},
        #         {"role": "user", "content": text}
        #     ]
        # )
        # return json.loads(response.choices[0].message.content)
        pass

    def _analyze_with_gemini(self, text: str) -> dict:
        """
        Google Gemini API를 사용하여 분석하는 로직
        (사전 준비: pip install google-generativeai)
        """
        # import google.generativeai as genai
        # genai.configure(api_key=self.api_key)
        # model = genai.GenerativeModel('gemini-pro')
        # prompt = f"다음 일기를 읽고 감정, 요약, 키워드 3개, 조언을 JSON 형태로 분석해줘:\n{text}"
        # response = model.generate_content(prompt)
        # return json.loads(response.text)
        pass

    def _mock_analysis(self, text: str) -> dict:
        """API 연동 전, 또는 테스트를 위한 임시 반환 함수"""
        return {
            "sentiment": "긍정",
            "summary": "오늘 하루는 전반적으로 평온하고 긍정적인 일이 많았습니다.",
            "keywords": ["휴식", "대화", "평온"],
            "feedback": "오늘 하루도 수고 많으셨습니다. 앞으로도 이런 여유를 즐기시길 바라요!",
            "text_length": len(text)
        }

if __name__ == "__main__":
    # 간단한 테스트 코드
    analyzer = AIAnalyzer()
    sample_text = "오늘은 오랜만에 친구들을 만나서 맛있는 것도 먹고 수다도 떨었다. 스트레스가 싹 풀리는 정말 즐거운 하루였다."
    
    result = analyzer.analyze(sample_text)
    
    print("=== 일기 분석 결과 ===")
    print(json.dumps(result, indent=4, ensure_ascii=False))