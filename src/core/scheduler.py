import os
import sys
import subprocess
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# 프로젝트 루트 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(current_dir))

def run_script(script_path):
    """스크립트를 서브프로세스로 실행"""
    if not os.path.exists(script_path):
         print(f"⚠️ [Skip] 파일이 없습니다: {script_path}")
         return

    rel_path = os.path.relpath(script_path, PROJECT_ROOT)
    print(f"\n🚀 [Scheduler] Executing: {rel_path}")
    
    # PYTHONPATH 설정
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    
    try:
        # sys.executable을 사용하여 현재 가상환경의 파이썬 사용
        subprocess.run([sys.executable, script_path], check=True, env=env)
        print(f"✅ [Scheduler] Finished: {rel_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ [Scheduler] Error in {rel_path}: {e}")
    except Exception as e:
        print(f"⚠️ [Scheduler] Unexpected error: {e}")

def run_full_batch():
    """모든 수집기 및 분석기 실행 (run_all.py 로직)"""
    print("="*60)
    print("⏰ [Scheduler] Starting Full Batch Job")
    print("="*60)

    start_time = time.time()
    COLLECTORS_DIR = os.path.join(PROJECT_ROOT, "src", "collectors")
    CORE_DIR = os.path.join(PROJECT_ROOT, "src", "core")

    # [1. 기초 환경 & 거시 경제]
    step1 = [
        "weather_collector.py",
        "macro_collector.py"
    ]

    # [2. 실물 자산 & 트렌드]
    step2 = [
        "real_estate_collector.py",
        "commercial_area_collector.py",
        "onbid_collector.py",
        "crypto_onchain_collector.py",
        "pdf_auto_collector.py",
        "search_collector.py",
        "ipo_collector.py",
        "global_ipo_collector.py"
    ]

    # [3. 뉴스 & 여론 & 거장]
    step3 = [
        "collector.py",
        "community_collector.py",
        "email_collector.py",
        "guru_collector.py"
    ]

    # 실행 순서
    all_scripts = step1 + step2 + step3
    
    # Collector 실행
    for script_name in all_scripts:
        script_path = os.path.join(COLLECTORS_DIR, script_name)
        run_script(script_path)
        time.sleep(1) 

    # [4. 종합 분석]
    print("\n" + "-"*60)
    print("🧠 [Scheduler] Running Analyst Agent")
    print("-" * 60)
    run_script(os.path.join(CORE_DIR, "analyst.py"))

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n🎉 [Scheduler] Batch Job Completed in {duration:.2f}s")

# 스케줄러 인스턴스 생성
scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        # 1. 매일 아침 7시에 전체 실행
        scheduler.add_job(
            run_full_batch,
            CronTrigger(hour=7, minute=0),
            id="daily_batch_job",
            replace_existing=True
        )
        
        # 2. (선택사항) 앱 시작 시 1분 뒤에 한 번 실행 (테스트용, 필요 없으면 주석 처리)
        # scheduler.add_job(
        #     run_full_batch,
        #     'date',
        #     run_date=datetime.now() + timedelta(minutes=1),
        #     id="startup_check"
        # )

        scheduler.start()
        print("✅ Scheduler started. Daily batch scheduled at 07:00.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Scheduler shut down.")
