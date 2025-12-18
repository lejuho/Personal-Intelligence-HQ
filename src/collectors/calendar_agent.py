import holidays
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta, TH, FR

class EconomicCalendar:
    def __init__(self):
        self.today = date.today()
        self.year = self.today.year
        self.kr_holidays = holidays.KR(years=self.year) # type: ignore # 한국 공휴일
        self.us_holidays = holidays.US(years=self.year) # type: ignore # 미국 공휴일
        self.cn_holidays = holidays.CN(years=self.year) # type: ignore # 중국 중추절 확인용

    def get_variable_events(self):
        """날짜가 매년 바뀌는 경제 이벤트 계산"""
        events = {}

        # 1. 미국: 땡스기빙 & 블랙프라이데이
        # 땡스기빙: 11월 4번째 목요일
        thanksgiving = date(self.year, 11, 1) + relativedelta(weekday=TH(4))
        events[thanksgiving] = "🇺🇸 Thanksgiving (추수감사절) - 미 증시 휴장, 소비 시즌 시작"
        
        # 블랙프라이데이: 땡스기빙 다음날 (금요일)
        black_friday = thanksgiving + timedelta(days=1)
        events[black_friday] = "🛍️ Black Friday (블랙프라이데이) - 연중 최대 소비 대목 (유통/물류)"

        # 2. 한국: 수능 (11월 3번째 목요일)
        suneung = date(self.year, 11, 1) + relativedelta(weekday=TH(3))
        events[suneung] = "🇰🇷 수능 (CSAT) - 증시 개장 1시간 지연, 내수 소비 영향"

        return events

    def get_fixed_events(self):
        """날짜가 고정된 상업/문화 이벤트"""
        # 월/일 : (이벤트명, 경제적 의미)
        return {
            (2, 14): "🍫 Valentine's Day - 제과/유통 매출 증가",
            (5, 5):  "🎈 어린이날 (Children's Day) - 완구/테마파크/여행 성수기",
            (7, 4):  "🇺🇸 Independence Day - 미 증시 휴장, 여행/소비 증가",
            (10, 1): "🇩🇪 Oktoberfest (옥토버페스트 시즌) - 주류/관광 (9월 말~10월 초)",
            (11, 11): "🇨🇳 광군제(Singles' Day) & 🇰🇷 빼빼로데이 - 이커머스 최대 매출 발생일",
            (12, 25): "🎄 Christmas - 연말 쇼핑 시즌 클라이맥스"
        }

    def get_lunar_events(self):
        """음력 기반 이벤트 (설날, 추석) - holidays 라이브러리 활용"""
        events = {}
        
        # 한국 공휴일에서 설날/추석 추출
        for dt, name in self.kr_holidays.items():
            if "Lunar New Year" in name or "Seollal" in name:
                events[dt] = "🧧 설날 (Seollal) - 증시 휴장, 현금 수요 증가"
            elif "Chuseok" in name:
                events[dt] = "🌕 추석 (Chuseok) - 증시 휴장, 선물세트/유통"
        
        return events

    def get_upcoming_impact(self, days_ahead=14):
        """향후 N일 내에 있는 경제적 파급력 있는 날짜 추출"""
        report = []
        
        variable_evts = self.get_variable_events()
        fixed_evts = self.get_fixed_events()
        lunar_evts = self.get_lunar_events()

        for i in range(days_ahead + 1):
            target_date = self.today + timedelta(days=i)
            
            # 1. 가변 이벤트 체크
            if target_date in variable_evts:
                d_day = "D-Day" if i == 0 else f"D-{i}"
                report.append(f"- [{d_day}] {variable_evts[target_date]}")

            # 2. 고정 이벤트 체크
            if (target_date.month, target_date.day) in fixed_evts:
                d_day = "D-Day" if i == 0 else f"D-{i}"
                report.append(f"- [{d_day}] {fixed_evts[(target_date.month, target_date.day)]}")

            # 3. 음력 이벤트 체크
            if target_date in lunar_evts:
                d_day = "D-Day" if i == 0 else f"D-{i}"
                report.append(f"- [{d_day}] {lunar_evts[target_date]}")

        if not report:
            return "특이한 경제 이벤트 없음."
        
        return "\n".join(report)

# 외부에서 호출할 함수
def get_market_seasonality():
    cal = EconomicCalendar()
    events = cal.get_upcoming_impact()
    
    # 계절 정보 추가
    month = date.today().month
    season = "겨울"
    if 3 <= month <= 5: season = "봄"
    elif 6 <= month <= 8: season = "여름"
    elif 9 <= month <= 11: season = "가을"

    return f"""
    [Economic Calendar Watch (Season: {season})]
    {events}
    (지시: 위 이벤트가 관련 주식(유통, 물류, 식품 등)이나 시장 유동성에 미칠 영향을 반드시 고려해.)
    """

if __name__ == "__main__":
    print(get_market_seasonality())