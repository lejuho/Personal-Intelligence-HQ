import requests
import json
import os
import sys
from datetime import datetime
# 1. 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from src.config import paths

# --- [설정] ---
SAVE_DIR = paths.WEATHER_DATA_DIR
# Directory creation is handled in config/paths.py

def load_secrets():
    try:
        with open(paths.SECRETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"오류: {paths.SECRETS_FILE} 파일을 찾을 수 없습니다.")
        return {}

secrets = load_secrets()
API_KEY = secrets.get("OPENWEATHERMAP_API_KEY", "") # 여기에 키 입력

# 감시할 핵심 경제 거점 (위도, 경도)
WATCH_LOCATIONS = {
    "US_Gulf_Coast": {"lat": 29.3, "lon": -94.8, "desc": "에너지(원유) 허브 - 허리케인 감시"},
    "US_Corn_Belt": {"lat": 41.6, "lon": -93.6, "desc": "곡물(옥수수/대두) 생산지 - 가뭄/홍수 감시"},
    "Brazil_Coffee": {"lat": -21.2, "lon": -47.8, "desc": "커피/설탕 생산지 - 서리/가뭄 감시"},
    "KR_Seoul": {"lat": 37.5, "lon": 126.9, "desc": "한국 내수 소비 중심지 - 날씨 마케팅"},
    "NY_WallStreet": {"lat": 40.7, "lon": -74.0, "desc": "미국 금융 중심지 - 심리적 영향"}
}

def get_weather_report():
    report_lines = []
    
    for name, loc in WATCH_LOCATIONS.items():
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={loc['lat']}&lon={loc['lon']}&appid={API_KEY}&units=metric"
        
        try:
            res = requests.get(url).json()
            
            # 주요 데이터 추출
            weather_main = res['weather'][0]['main'] # Rain, Clear, Snow, Extreme 등
            desc = res['weather'][0]['description']
            temp = res['main']['temp']
            wind_speed = res['wind']['speed']
            
            # [핵심] '특이 사항'이 있을 때만 강조 표시 (노이즈 필터링)
            warning_flag = ""
            if weather_main in ["Thunderstorm", "Tornado", "Squall"]:
                warning_flag = "🚨 [기상 악화]"
            elif "rain" in desc and res.get('rain', {}).get('1h', 0) > 10: # 시간당 10mm 이상 폭우
                warning_flag = "☔ [폭우 주의]"
            elif wind_speed > 20: # 강풍
                warning_flag = "🌪️ [태풍급 강풍]"
            elif temp > 35:
                warning_flag = "🔥 [폭염]"
            elif temp < -10:
                warning_flag = "❄️ [한파]"

            # 리포트 라인 생성
            line = f"- **{name} ({loc['desc']}):** {warning_flag} {weather_main} ({desc}), {temp}°C, 바람 {wind_speed}m/s"
            report_lines.append(line)
            
        except Exception as e:
            print(f"⚠️ {name} 날씨 조회 실패: {e}")
            continue

    # 결과 텍스트 생성
    full_report = "[글로벌 주요 경제 거점 기상 현황]\n" + "\n".join(report_lines)
    
    # 파일 저장 (매번 덮어쓰기 - 최신 날씨만 중요하므로)
    # analyst.py가 읽기 쉽게 txt로 저장
    with open(SAVE_DIR / "current_weather.txt", "w", encoding="utf-8") as f:
        f.write(full_report)
        
    print("✅ 기상 정보 업데이트 완료.")
    return full_report

if __name__ == "__main__":
    get_weather_report()
