from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


class EmotionAnalytics:
    """감정 데이터를 분석하고 시각화하는 클래스"""
    
    # 감정 레벨 (0-100)
    EMOTION_LEVELS = {
        "매우 행복": 90,
        "행복": 75,
        "보통": 50,
        "슬픔": 25,
        "매우 슬픔": 10
    }
    
    EMOTION_LEVELS_EN = {
        "very happy": 90,
        "happy": 75,
        "neutral": 50,
        "sad": 25,
        "very sad": 10
    }
    
    EMOTION_EMOJIS = {
        90: "😄",
        75: "😊",
        50: "😐",
        25: "😞",
        10: "😢"
    }
    
    def __init__(self, data_file: str = "emotions.json", password_key: Optional[str] = None, is_test: bool = False):
        self.password_key = password_key
        self.is_test = is_test
        if is_test:
            self.emotions_data = {}
        else:
            self.emotions_data = self._load_emotions(password_key)
    
    def _load_emotions(self, password_key: Optional[str] = None) -> Dict:
        """vault/index.json에서 감정 데이터를 읽어옵니다"""
        from storage import _load_index
        index = _load_index(password_key)
        emotions: Dict = {}
        for entry in index:
            date = entry.get("date")
            if not date:
                continue
            emotion_str = entry.get("emotion", "보통")
            
            # 감정 명칭 정규화 (공백 제거 및 키워드 매칭 완화)
            emotion_str_clean = emotion_str.strip()
            if "매우 행복" in emotion_str_clean:
                level = 90
            elif "행복" in emotion_str_clean:
                level = 75
            elif "매우 슬픔" in emotion_str_clean:
                level = 10
            elif "슬픔" in emotion_str_clean:
                level = 25
            elif "보통" in emotion_str_clean or "평온" in emotion_str_clean or "무난" in emotion_str_clean:
                level = 50
            else:
                level = self.EMOTION_LEVELS.get(emotion_str_clean) or self.EMOTION_LEVELS_EN.get(emotion_str_clean.lower(), 50)
                
            emotions[date] = [{
                "level": level,
                "content": entry.get("summary", ""),
                "timestamp": date + "T00:00:00"
            }]
        return emotions

    def add_emotion(self, emotion_level: int, content: str = "",
                   timestamp: Optional[str] = None, password_key: Optional[str] = None) -> bool:
        """감정 데이터를 vault에 저장합니다"""
        if not 0 <= emotion_level <= 100:
            print("❌ 감정 레벨은 0-100 사이여야 합니다.")
            return False

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        date_key = timestamp[:10]
        emotion_str = self._level_to_emotion_str(emotion_level)

        if not self.is_test:
            from storage import save_diary
            save_diary(
                date_str=date_key,
                title=f"{date_key} 감정 기록",
                encrypted_content=content,
                emotion=emotion_str,
                summary=content[:80] if content else "",
                tags=[],
                password_key=password_key
            )

        # 로컬 캐시 갱신
        self.emotions_data[date_key] = [{
            "level": emotion_level,
            "content": content,
            "timestamp": timestamp
        }]
        return True

    @staticmethod
    def _level_to_emotion_str(level: int) -> str:
        if level >= 80:
            return "매우 행복"
        elif level >= 60:
            return "행복"
        elif level >= 40:
            return "보통"
        elif level >= 20:
            return "슬픔"
        else:
            return "매우 슬픔"
    
    def get_week_emotions(self, days: int = 7) -> List[Tuple[str, float]]:
        """
        지난 N일간의 감정 데이터를 평균값으로 반환합니다
        
        Args:
            days: 조회할 일수 (기본값: 7)
        
        Returns:
            [(날짜, 평균 감정값)] 리스트
        """
        result = []
        today = datetime.now().date()
        
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_key = date.isoformat()
            
            if date_key in self.emotions_data:
                emotions = self.emotions_data[date_key]
                avg_level = sum(e['level'] for e in emotions) / len(emotions)
                result.append((date_key, avg_level))
            else:
                result.append((date_key, None))
        
        return result
    
    def get_week_stats(self, days: int = 7) -> Dict:
        """
        지난 N일간의 감정 통계를 반환합니다
        
        Args:
            days: 조회할 일수 (기본값: 7)
        
        Returns:
            통계 딕셔너리
        """
        week_emotions = self.get_week_emotions(days)
        valid_emotions = [level for _, level in week_emotions if level is not None]
        
        if not valid_emotions:
            return {
                "avg": 0,
                "max": 0,
                "min": 0,
                "count": 0,
                "trend": "데이터 없음"
            }
        
        avg = sum(valid_emotions) / len(valid_emotions)
        max_level = max(valid_emotions)
        min_level = min(valid_emotions)
        
        # 추세 분석
        if len(valid_emotions) >= 2:
            first_half = sum(valid_emotions[:len(valid_emotions)//2]) / (len(valid_emotions)//2)
            second_half = sum(valid_emotions[len(valid_emotions)//2:]) / (len(valid_emotions) - len(valid_emotions)//2)
            
            if second_half > first_half + 5:
                trend = "📈 상승"
            elif second_half < first_half - 5:
                trend = "📉 하강"
            else:
                trend = "➡️ 안정"
        else:
            trend = "데이터 부족"
        
        return {
            "avg": round(avg, 1),
            "max": round(max_level, 1),
            "min": round(min_level, 1),
            "count": len(valid_emotions),
            "trend": trend
        }
    
    def plot_ascii_chart(self, days: int = 7, width: int = 80, height: int = 20) -> str:
        """
        ASCII 차트로 감정 변화를 시각화합니다
        
        Args:
            days: 조회할 일수
            width: 차트 너비 (문자)
            height: 차트 높이 (문자)
        
        Returns:
            ASCII 차트 문자열
        """
        week_emotions = self.get_week_emotions(days)
        values = [level if level is not None else 0 for _, level in week_emotions]
        dates = [date for date, _ in week_emotions]
        
        if not values or max(values) == 0:
            return "📊 표시할 데이터가 없습니다."
        
        # 정규화: 0-100을 0-height로 변환
        max_val = max(values) if max(values) > 0 else 1
        normalized = [int((v / 100) * height) for v in values]
        
        # 차트 생성
        chart_lines = []
        
        # 제목
        chart_lines.append("📈 최근 일주일 감정 변화".center(width))
        chart_lines.append("=" * width)
        
        # Y축 레이블과 차트
        for y in range(height, 0, -1):
            line = f"{y*5:3d}% │ "  # Y축 레이블 (5단위)
            
            for x, norm_val in enumerate(normalized):
                if norm_val >= y:
                    # 감정값에 따른 블록 선택
                    if values[x] >= 80:
                        char = "🟥"  # 매우 행복
                    elif values[x] >= 60:
                        char = "🟨"  # 행복
                    elif values[x] >= 40:
                        char = "🟩"  # 보통
                    elif values[x] >= 20:
                        char = "🟦"  # 슬픔
                    else:
                        char = "🟪"  # 매우 슬픔
                else:
                    char = "   "  # 빈 공간
                
                line += char + " "
            
            chart_lines.append(line)
        
        # X축
        x_axis = "  0% └─"
        for _ in range(len(normalized)):
            x_axis += "────"
        chart_lines.append(x_axis)
        
        # X축 레이블 (날짜)
        date_line = "      "
        for i, date in enumerate(dates):
            day = date.split('-')[2]  # DD 추출
            date_line += f"{day:4s}"
        chart_lines.append(date_line)
        
        # 범례
        chart_lines.append("─" * width)
        legend = "범례: 🟥 매우행복(80+) │ 🟨 행복(60-79) │ 🟩 보통(40-59) │ 🟦 슬픔(20-39) │ 🟪 매우슬픔(0-19)"
        if len(legend) > width:
            chart_lines.append(legend[:width])
            chart_lines.append(legend[width:])
        else:
            chart_lines.append(legend)
        
        return "\n".join(chart_lines)
    
    def plot_ascii_bar_chart(self, days: int = 7, width: int = 80) -> str:
        """
        ASCII 막대 그래프로 감정 변화를 시각화합니다
        
        Args:
            days: 조회할 일수
            width: 차트 너비 (문자)
        
        Returns:
            ASCII 막대 그래프 문자열
        """
        week_emotions = self.get_week_emotions(days)
        
        if not week_emotions or all(level is None for _, level in week_emotions):
            return "📊 표시할 데이터가 없습니다."
        
        chart_lines = []
        chart_lines.append("📊 일주일 감정 막대 그래프".center(width))
        chart_lines.append("=" * width)
        
        bar_width = max(1, (width - 20) // len(week_emotions))
        
        for date, level in week_emotions:
            day = date.split('-')[2]  # DD 추출
            
            if level is None:
                bar = "[데이터 없음]"
                emoji = "  "
                level_str = "N/A"
            else:
                bar_length = int((level / 100) * bar_width)
                
                # 감정에 따른 문자 선택
                if level >= 80:
                    bar_char = "█"
                elif level >= 60:
                    bar_char = "▓"
                elif level >= 40:
                    bar_char = "▒"
                elif level >= 20:
                    bar_char = "░"
                else:
                    bar_char = "▁"
                
                bar = bar_char * bar_length
                emoji = self.EMOTION_EMOJIS.get(int(level // 10 * 10), "😐")
                level_str = f"{level:.0f}%"
            
            line = f"{day} {emoji} │ {bar} {level_str}".ljust(width)
            chart_lines.append(line)
        
        chart_lines.append("─" * width)
        
        return "\n".join(chart_lines)
    
    def plot_matplotlib_chart(self, days: int = 7, show: bool = True) -> Optional[object]:
        """
        matplotlib을 사용하여 차트를 생성합니다
        
        Args:
            days: 조회할 일수
            show: 차트 표시 여부
        
        Returns:
            matplotlib figure 객체 (표시하지 않으면 None)
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import matplotlib.font_manager as fm
            from datetime import datetime as dt
        except ImportError:
            return "matplotlib이 설치되지 않았습니다. 'pip install matplotlib'을 실행하세요."

        # 한글 폰트 설정
        korean_fonts = ['AppleGothic', 'Apple SD Gothic Neo', 'NanumGothic', 'Malgun Gothic']
        available = [f.name for f in fm.fontManager.ttflist]
        for font in korean_fonts:
            if font in available:
                plt.rcParams['font.family'] = font
                break
        plt.rcParams['axes.unicode_minus'] = False
        
        week_emotions = self.get_week_emotions(days)
        dates = [dt.fromisoformat(date) for date, _ in week_emotions]
        values = [level if level is not None else 0 for _, level in week_emotions]
        
        if not values or max(values) == 0:
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 라인 차트
        ax1.plot(dates, values, marker='o', linewidth=2, markersize=8, color='#4A90E2')
        ax1.fill_between(dates, values, alpha=0.3, color='#4A90E2')
        ax1.set_title('최근 일주일 감정 변화 추이', fontsize=14, fontweight='bold', pad=20)
        ax1.set_ylabel('감정 레벨', fontsize=11)
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 막대 차트
        colors = ['#FF6B6B' if v >= 80 else '#FFA500' if v >= 60 else '#90EE90' 
                  if v >= 40 else '#87CEEB' if v >= 20 else '#8B4789' for v in values]
        ax2.bar(dates, values, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_title('일일 감정 분포', fontsize=14, fontweight='bold', pad=20)
        ax2.set_ylabel('감정 레벨', fontsize=11)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if show:
            plt.show()
        
        return fig
    
    def display_summary(self, days: int = 7) -> str:
        """
        감정 분석 요약을 반환합니다
        
        Args:
            days: 조회할 일수
        
        Returns:
            요약 문자열
        """
        stats = self.get_week_stats(days)
        
        summary_lines = []
        summary_lines.append("\n" + "="*60)
        summary_lines.append(f"📊 지난 {days}일 감정 분석 요약")
        summary_lines.append("="*60)
        summary_lines.append(f"📈 평균 감정: {stats['avg']:.1f}% 😊")
        summary_lines.append(f"⬆️  최고 감정: {stats['max']:.1f}%")
        summary_lines.append(f"⬇️  최저 감정: {stats['min']:.1f}%")
        summary_lines.append(f"📝 기록 일수: {stats['count']}일")
        summary_lines.append(f"📊 감정 추세: {stats['trend']}")
        summary_lines.append("="*60 + "\n")
        
        return "\n".join(summary_lines)


# 테스트 코드
if __name__ == "__main__":
    print("🚀 EmotionAnalytics 테스트 시작\n")
    
    # Analytics 인스턴스 생성 (테스트 모드로 가짜 데이터가 메모리에만 생성됨)
    analytics = EmotionAnalytics(is_test=True)
    
    # 테스트 데이터 추가 (지난 7일간)
    print("📝 테스트 데이터를 추가합니다...\n")
    
    base_date = datetime.now() - timedelta(days=6)
    test_data = [
        (45, "오늘 기분이 나쁜 날이었어."),
        (60, "일이 잘 풀렸던 하루."),
        (75, "좋은 소식을 받았다!"),
        (50, "평범한 하루였다."),
        (85, "최고의 하루였어! 모든 것이 완벽했다."),
        (40, "스트레스가 많은 날."),
        (70, "괜찮은 하루를 보냈다."),
    ]
    
    for i, (level, content) in enumerate(test_data):
        timestamp = (base_date + timedelta(days=i)).date().isoformat() + "T10:00:00"
        analytics.add_emotion(level, content, timestamp)
        print(f"  ✅ {timestamp[:10]} - 감정 {level}% 추가")
    
    print("\n" + "="*60)
    print("\n📊 감정 분석 요약:")
    print(analytics.display_summary())
    
    # ASCII 차트 출력 (라인 차트)
    print("\n📈 라인 차트:")
    print(analytics.plot_ascii_chart())
    
    # ASCII 차트 출력 (막대 그래프)
    print("\n\n📊 막대 그래프:")
    print(analytics.plot_ascii_bar_chart())
    
    # matplotlib 차트 (설치된 경우)
    print("\n\n🎨 matplotlib 차트 생성 (설치된 경우 표시됨):")
    try:
        fig = analytics.plot_matplotlib_chart(show=False)
        print("✅ matplotlib 차트가 생성되었습니다!")
        import matplotlib.pyplot as plt
        plt.savefig("emotion_chart.png", dpi=100, bbox_inches='tight')
        plt.close()
        print("💾 emotion_chart.png로 저장되었습니다.")
    except Exception as e:
        print(f"⚠️  matplotlib 사용 불가: {e}")
    
    # 주간 감정 데이터
    print("\n\n📅 주간 감정 데이터:")
    week_data = analytics.get_week_emotions()
    for date, level in week_data:
        if level is not None:
            emoji = analytics.EMOTION_EMOJIS.get(int(level // 10 * 10), "😐")
            print(f"  {date}: {level:.1f}% {emoji}")
        else:
            print(f"  {date}: [데이터 없음]")

