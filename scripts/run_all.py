import subprocess
import sys
import time
import os


# [수정 1] 프로젝트 루트 경로를 명확하게 계산 (scripts 폴더의 상위 폴더)
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(current_dir)

def run_script(script_path):
    # script_path는 이제 절대 경로로 들어옵니다.
    
    # Check existence
    if not os.path.exists(script_path):
         print(f"⚠️ [Skip] 파일이 없습니다: {script_path}")
         return

    # 출력용 경로 (보기 좋게 상대 경로로 표시)
    rel_path = os.path.relpath(script_path, PROJECT_ROOT)
    print(f"\n🚀 [{rel_path}] 실행 중...")
    
    # [수정 2] PYTHONPATH 설정 (이미 계산해둔 PROJECT_ROOT 사용)
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    
    try:
        subprocess.run([sys.executable, script_path], check=True, env=env)
        print(f"✅ [{rel_path}] 완료.")
    except subprocess.CalledProcessError:
        print(f"❌ [{rel_path}] 실행 중 오류 발생! (건너뜁니다)")
    except Exception as e:
        print(f"⚠️ 예상치 못한 오류: {e}")

def main():
    start_time = time.time()
    
    print("="*60)
    print("🤖 Personal Intelligence System : Full Batch Run")
    print(f"📂 Project Root: {PROJECT_ROOT}")
    print("="*60)

    # [수정 3] 경로를 PROJECT_ROOT 기준 절대 경로로 변경
    COLLECTORS_DIR = os.path.join(PROJECT_ROOT, "src", "collectors")
    CORE_DIR = os.path.join(PROJECT_ROOT, "src", "core")

    # [1. 기초 환경 & 거시 경제]
    collectors_step1 = [
        os.path.join(COLLECTORS_DIR, "weather_collector.py"),       
        os.path.join(COLLECTORS_DIR, "macro_collector.py"),         
    ]

    # [2. 실물 자산 & 트렌드]
    collectors_step2 = [
        os.path.join(COLLECTORS_DIR, "real_estate_collector.py"),      
        os.path.join(COLLECTORS_DIR, "commercial_area_collector.py"),  
        os.path.join(COLLECTORS_DIR, "onbid_collector.py"),               
        os.path.join(COLLECTORS_DIR, "crypto_onchain_collector.py"),   
        os.path.join(COLLECTORS_DIR, "pdf_auto_collector.py"),
        os.path.join(COLLECTORS_DIR, "search_collector.py"),
        # 👇 [NEW] IPO 수집기 2종 추가
        os.path.join(COLLECTORS_DIR, "ipo_collector.py"),         # 한국/미국 캘린더
        os.path.join(COLLECTORS_DIR, "global_ipo_collector.py")   # 글로벌 트렌드
    ]

    # [3. 뉴스 & 여론 & 거장]
    collectors_step3 = [
        # ... (기존과 동일) ...
        os.path.join(COLLECTORS_DIR, "collector.py"),
        os.path.join(COLLECTORS_DIR, "community_collector.py"),
        os.path.join(COLLECTORS_DIR, "email_collector.py"),
        os.path.join(COLLECTORS_DIR, "guru_collector.py")
    ]

    all_collectors = collectors_step1 + collectors_step2 + collectors_step3
    
    for script in all_collectors:
        run_script(script)
        time.sleep(1) 

    # [4. 종합 분석]
    print("\n" + "-"*60)
    print("🧠 데이터 융합 및 전략 분석 시작 (Analyst Agent)")
    print("-" * 60)
    
    run_script(os.path.join(CORE_DIR, "analyst.py"))

    end_time = time.time()
    print("\n" + "="*60)
    print(f"🎉 모든 작업 완료! (소요시간: {end_time - start_time:.2f}초)")
    print("="*60)

if __name__ == "__main__":
    main()