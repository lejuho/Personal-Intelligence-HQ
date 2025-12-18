import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

if project_root not in sys.path:
    sys.path.append(project_root)

# ---------------------------------------------------------
# [2] 안전한 모듈 임포트 (Safe Import)
# ---------------------------------------------------------
try:
    from src.config import paths
except ImportError:
    paths = None

# OKXAdvisor 불러오기 (에러 방지용 try-except)
OKXAdvisor = None
try:
    from src.core.okx_advisor import OKXAdvisor
except ImportError as e:
    pass # 모듈 로드 실패 시, 아래 UI에서 경고 메시지 처리

# ---------------------------------------------------------
# [3] 기본 설정 및 데이터 로드
# ---------------------------------------------------------
st.set_page_config(page_title="Personal Intelligence HQ", layout="wide", page_icon="🧠")

# DB 파일 경로 설정 (Robust)
if paths and hasattr(paths, 'DB_FILE'):
    DB_FILE = str(paths.DB_FILE)
else:
    # fallback: 프로젝트 루트의 my_chat_log.db
    DB_FILE = os.path.join(project_root, "data", "database", "my_chat_log.db")

SESSION_THRESHOLD_MIN = 30 

def load_chat_data():
    """채팅 로그 로드"""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM chat_logs ORDER BY created_at DESC", conn)
        conn.close()
        if not df.empty:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
        return df
    except: return pd.DataFrame()

def load_latest_insight():
    """최신 전략 브리핑 로드"""
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT created_at, content FROM daily_insights ORDER BY created_at DESC LIMIT 1").fetchone()
        conn.close()
        return row
    except: return None

def process_sessions(df_24h):
    """채팅 세션 분석"""
    if df_24h.empty: return pd.DataFrame()
    df_sorted = df_24h.sort_values('created_at')
    df_sorted['time_diff'] = df_sorted['created_at'].diff()
    df_sorted['is_new_session'] = df_sorted['time_diff'] > timedelta(minutes=SESSION_THRESHOLD_MIN)
    df_sorted['is_new_session'] = df_sorted['is_new_session'].fillna(True)
    df_sorted['session_id'] = df_sorted['is_new_session'].cumsum()
    return df_sorted

# ---------------------------------------------------------
# [4] 메인 UI 구성
# ---------------------------------------------------------
st.title("🧠 Personal Intelligence & Trading HQ")
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 탭 메뉴 구성 (3개)
tab1, tab2, tab3 = st.tabs(["📊 전략 브리핑", "💰 AI 트레이딩 (OKX)", "🗂️ 사고 기록"])

# =========================================================
# Tab 1: 전략 브리핑 (Analyst Insight)
# =========================================================
with tab1:
    latest_insight = load_latest_insight()
    if latest_insight:
        insight_date, content = latest_insight
        st.info(f"📅 생성 시각: {insight_date}")
        st.markdown(content)
    else:
        st.warning("아직 생성된 브리핑이 없습니다. 'run_all.py'를 실행하세요.")

# =========================================================
# Tab 2: AI 트레이딩 (OKX + Fibonacci)
# =========================================================
with tab2:
    st.header("📈 비트코인(BTC) 실시간 AI 분석")
    
    if OKXAdvisor is None:
        st.error("⚠️ 트레이딩 모듈을 불러오지 못했습니다.")
        st.info("💡 해결 방법:")
        st.code("py -m pip install ccxt pandas plotly", language="bash")
        st.markdown("위 명령어를 터미널에 입력하여 라이브러리를 설치한 후, 다시 실행해주세요.")
    else:
        if st.button("🚀 시장 분석 및 신호 포착 (Click)", key="trade_btn"):
            with st.spinner("OKX 차트와 뉴스를 융합 분석 중입니다..."):
                try:
                    advisor = OKXAdvisor()
                    result = advisor.analyze()
                    
                    if result:
                        col1, col2 = st.columns([3, 1])
                        
                        # [좌측] 차트 + 피보나치
                        with col1:
                            df = result['market']['df']
                            fib = result['fib']
                            
                            fig = go.Figure(data=[go.Candlestick(
                                x=df['timestamp'], open=df['open'], high=df['high'],
                                low=df['low'], close=df['close'], name='BTC/USDT'
                            )])
                            
                            # 피보나치 라인
                            colors = {'0.618 (Golden)': 'green', '0.5 (Half)': 'yellow', '0.382': 'red'}
                            for level, price in fib.items():
                                color = colors.get(level, 'gray')
                                width = 2 if level in colors else 1
                                fig.add_hline(y=price, line_dash="dash", line_color=color, line_width=width,
                                              annotation_text=f"{level}: {price:.1f}", annotation_position="top right")

                            fig.update_layout(title="BTC/USDT 4H Chart", height=600, 
                                              xaxis_rangeslider_visible=False, template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)

                        # [우측] AI 어드바이저 & 잔고
                        with col2:
                            st.subheader("🤖 AI Signal")
                            st.metric("현재가", f"{result['market']['current_price']:.1f}")
                            st.metric("RSI (14)", f"{result['market']['rsi']:.1f}")
                            
                            st.divider()
                            st.markdown("##### 💡 매매 전략")
                            st.info(result['ai_comment'])
                            
                            st.divider()
                            st.subheader("💼 내 지갑")
                            st.metric("가용 잔고", f"{float(result['account']['balance']):.2f} USDT")
                            st.caption(f"포지션: {result['account']['position']}")
                    else:
                        st.error("데이터 분석 실패 (API 키 또는 네트워크 확인)")
                except Exception as e:
                    st.error(f"실행 중 오류 발생: {e}")

# =========================================================
# Tab 3: 사고 기록 (Chat History)
# =========================================================
with tab3:
    df = load_chat_data()
    
    # 1. 24시간 활동 요약
    st.subheader("🌊 나의 사고 흐름 (Recent 24h)")
    if not df.empty:
        now = datetime.now()
        df_24h = df[df['created_at'] >= (now - timedelta(hours=24))].copy()
        
        if not df_24h.empty:
            df_sessions = process_sessions(df_24h)
            
            # KPI
            c1, c2, c3 = st.columns(3)
            c1.metric("질문 수", f"{len(df_sessions)}개")
            c2.metric("주제 전환", f"{df_sessions['session_id'].nunique()}회")
            c3.metric("집중 시간", f"{df_sessions['created_at'].dt.hour.mode()[0]}:00 경")
            
            # 타임라인 차트
            session_summary = df_sessions.groupby('session_id').agg(
                start=('created_at', 'min'), end=('created_at', 'max'),
                first_q=('question', 'first'), count=('question', 'count')
            ).reset_index()
            session_summary.loc[session_summary['start'] == session_summary['end'], 'end'] += timedelta(minutes=5)
            
            fig = px.timeline(session_summary, x_start="start", x_end="end", y="first_q", color="count",
                              labels={'first_q': '주제'}, color_continuous_scale='Viridis')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # 2. 전체 기록 검색
    st.divider()
    st.subheader("📂 전체 기록 보관소")
    search = st.text_input("🔍 키워드 검색", placeholder="기술, 투자, 엔비디아...")
    
    if search:
        res = df[df['question'].str.contains(search, case=False, na=False) | 
                 df['answer'].str.contains(search, case=False, na=False)]
        st.success(f"{len(res)}건 검색됨")
        for _, row in res.iterrows():
            with st.expander(f"[{row['date']}] {row['question'][:40]}..."):
                st.write(row['answer'])
    else:
        if not df.empty:
            dates = sorted(df['date'].unique(), reverse=True)
            sel_date = st.selectbox("날짜별 보기", dates)
            day_data = df[df['date'] == sel_date]
            for _, row in day_data.iterrows():
                with st.expander(f"{row['created_at'].strftime('%H:%M')} | {row['question'][:50]}..."):
                    st.write(row['answer'])