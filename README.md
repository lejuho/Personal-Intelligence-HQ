# 🧠 Personal Intelligence HQ

**Data-Driven Investment & Career Strategy System**

이 프로젝트는 흩어져 있는 투자 정보(부동산, 거시경제, 암호화폐)와 기술 트렌드(AI, 채용)를 자동으로 수집하고, LLM 기반 AI 에이전트가 이를 융합하여 **개인화된 일일 전략 리포트(Daily Briefing)**를 제공하는 시스템입니다.

## ✨ Key Features

### 1. 🤖 Data Collectors (자동 수집)
다양한 소스에서 원시 데이터를 수집하여 분석 가능한 형태로 가공합니다.
*   **Asset:** 부동산(온비드 공매, 실거래가), 상권 분석, 암호화폐 온체인 데이터, IPO 일정
*   **Macro:** 날씨, 거시경제 지표 (금리, 환율 등)
*   **Tech & Trends:** AI 뉴스, 기술 블로그, 커뮤니티 여론, 글로벌 리포트 (PDF)

### 2. 🧠 AI Analyst (전략 분석)
수집된 데이터를 다단계(Multi-Stage)로 분석하여 통찰을 도출합니다.
*   **Stage 1 (Asset):** 부동산/경매 데이터에서 저평가 기회 및 상권 트렌드 분석
*   **Stage 2 (Tech):** 채용 시장과 기술 뉴스에서 뜨는 스택 및 커리어 기회 포착
*   **Stage 3 (Fusion):** 두 분석 결과를 '투자의 거장(Gurus)' 관점과 결합하여 최종 **Action Plan** 도출

### 3. 📊 Dashboard HQ
**Streamlit** 기반의 통합 대시보드에서 모든 정보를 시각화합니다.
*   **Daily Briefing:** 매일 아침 생성된 AI 전략 리포트 확인
*   **AI Trading:** 비트코인(BTC) 실시간 차트 분석 및 매매 신호 (OKX + Fibonacci + AI)
*   **Chat Memory:** 시스템과의 대화 및 사고 흐름 기록/검색

## 🚀 Quick Start (Docker)

Docker가 설치되어 있다면 단 한 줄로 실행 가능합니다.

```bash
# 컨테이너 실행 (백엔드 + 대시보드)
docker-compose up -d
```

*   **Dashboard:** [http://localhost:8501](http://localhost:8501)
*   **Backend API:** [http://localhost:8000](http://localhost:8000)

## 📂 Project Structure

*   `src/collectors/`: 데이터 수집 스크립트 모음
*   `src/core/analyst.py`: AI 분석 및 리포트 생성 엔진
*   `src/core/dashboard.py`: Streamlit 대시보드
*   `src/main.py`: FastAPI 서버 및 스케줄러 (배치 작업 관리)
*   `data/`: 수집된 데이터 및 DB 저장소 (Docker Volume으로 영구 저장)

## 🛠 Tech Stack
*   **Core:** Python 3.14, FastAPI
*   **AI:** Google Gemini Pro (via API)
*   **Data:** Pandas, SQLite, Plotly
*   **Infra:** Docker, Docker Compose
