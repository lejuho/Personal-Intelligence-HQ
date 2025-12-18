import ccxt
import pandas as pd
import sqlite3
import os
import sys
import google.generativeai as genai
from datetime import datetime

# 프로젝트 루트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from src.config import paths

# [설정] 본인의 OKX API 키 입력
OKX_API_KEY = "4dea57f7-d2cd-49d6-bcdb-1741d9a48c03"
OKX_SECRET_KEY = "1DB856061686277B4700BEE2FBF0D1AE"
OKX_PASSWORD = "Camping123^^"
GEMINI_API_KEY = "AIzaSyDT3-NHZr1KYFWgS77naMuHb4okAbIZmRc"

genai.configure(api_key=GEMINI_API_KEY)

class OKXAdvisor:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': OKX_API_KEY,
            'secret': OKX_SECRET_KEY,
            'password': OKX_PASSWORD,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.symbol = 'BTC/USDT:USDT'

    def get_market_sentiment(self):
        try:
            conn = sqlite3.connect(paths.DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM daily_insights ORDER BY created_at DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "시장 분석 데이터 없음"
        except: return "데이터 로드 실패"

    def get_market_data(self, timeframe='4h', limit=100):
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 지표 계산
            current_price = df['close'].iloc[-1]
            recent_high = df['high'].max()
            recent_low = df['low'].min()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]

            return {
                "df": df, # 차트 그리기용 전체 데이터
                "current_price": current_price,
                "recent_high": recent_high,
                "recent_low": recent_low,
                "rsi": rsi
            }
        except Exception as e:
            print(f"차트 오류: {e}")
            return None

    def get_account_status(self):
        try:
            balance = self.exchange.fetch_balance()
            usdt_free = balance['USDT']['free']
            positions = self.exchange.fetch_positions([self.symbol])
            
            pos_info = "없음"
            if positions:
                p = positions[0]
                if float(p['contracts']) > 0:
                    pos_info = f"{p['side'].upper()} (진입: {p['entryPrice']}, PNL: {p['unrealizedPnl']})"
            
            return {"balance": usdt_free, "position": pos_info}
        except: return {"balance": 0, "position": "조회 실패"}

    def analyze(self):
        """대시보드에서 호출할 메인 함수"""
        sentiment = self.get_market_sentiment()
        market = self.get_market_data()
        account = self.get_account_status()
        
        if not market: return None

        # 피보나치 계산
        high = market['recent_high']
        low = market['recent_low']
        diff = high - low
        fib = {
            "0.236": high - (diff * 0.236),
            "0.382": high - (diff * 0.382),
            "0.5 (Half)": high - (diff * 0.5),
            "0.618 (Golden)": high - (diff * 0.618),
            "0.786": high - (diff * 0.786)
        }

        # AI 프롬프트
        prompt = f"""
        당신은 '비트코인 선물 트레이딩 AI'입니다. 
        뉴스(심리)와 차트(기술)를 융합해 매매 전략을 제시하세요.

        [시장 심리] {sentiment[:500]}...
        [기술적 지표 (4시간봉)]
        - 현재가: {market['current_price']}
        - 추세: {'상승' if market['current_price'] > market['df']['close'].mean() else '하락'} (평균 대비)
        - RSI: {market['rsi']:.1f}
        
        [피보나치 레벨]
        - 0.382: {fib['0.382']:.1f}
        - 0.618 (중요): {fib['0.618 (Golden)']:.1f}

        [내 잔고] {account['balance']} USDT, 포지션: {account['position']}

        결과를 다음 형식으로 짧게 답변하세요:
        **판단:** [LONG / SHORT / 관망]
        **이유:** (한 문장 요약)
        **전략:** (진입가/손절가 추천)
        """
        
        model = genai.GenerativeModel("gemini-2.5-pro")
        try:
            response = model.generate_content(prompt)
            ai_comment = response.text
        except: ai_comment = "AI 분석 실패"

        return {
            "market": market,
            "fib": fib,
            "account": account,
            "ai_comment": ai_comment
        }