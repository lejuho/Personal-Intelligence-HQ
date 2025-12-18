import subprocess
import os

# 프로젝트 루트 경로 계산
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(current_dir)
BACKUP_PATH = os.path.join(PROJECT_ROOT, "data", "db_backup.sql")

def restore():
    if not os.path.exists(BACKUP_PATH):
        print(f"❌ 백업 파일을 찾을 수 없습니다: {BACKUP_PATH}")
        print("💡 'data' 폴더에 'db_backup.sql' 파일이 있는지 확인해주세요.")
        return

    print(f"🚀 Database 복구 시작 (기존 데이터가 덮어씌워질 수 있습니다)...")
    
    try:
        # docker exec -i 를 통해 sql 파일 내용을 psql로 전달
        with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
            subprocess.run(
                ["docker", "exec", "-i", "investment_postgres", "psql", "-U", "user", "-d", "investment_db"],
                stdin=f,
                check=True,
                shell=True
            )
        print("✅ 복구 완료! 이제 최신 데이터를 대시보드에서 확인하세요.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 복구 실패 (Docker 실행 확인 필요): {e}")
    except Exception as e:
        print(f"⚠️ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    restore()
