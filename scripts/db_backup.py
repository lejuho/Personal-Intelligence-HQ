import subprocess
import os
import sys

# 프로젝트 루트 경로 계산
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(current_dir)
BACKUP_PATH = os.path.join(PROJECT_ROOT, "data", "db_backup.sql")

def backup():
    print(f"🚀 Database 백업 시작...")
    print(f"📂 저장 경로: {BACKUP_PATH}")
    
    try:
        # docker exec 명령어를 통해 pg_dump 실행 결과를 파일로 저장
        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            subprocess.run(
                ["docker", "exec", "investment_postgres", "pg_dump", "-U", "user", "-d", "investment_db"],
                stdout=f,
                check=True,
                shell=True # Windows에서 명령어 인식을 위해 shell=True 사용
            )
        print("✅ 백업 완료! 이제 'data' 폴더를 옮기시면 됩니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 백업 실패 (Docker 실행 확인 필요): {e}")
    except Exception as e:
        print(f"⚠️ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    backup()
