import imaplib
import email
from email.header import decode_header
import os
import sys
import datetime

# ---------------------------------------------------------
# [1] 경로 및 설정
# ---------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from src.config import paths

# 저장 경로 (리포트 폴더에 저장하면 Analyst가 자동으로 읽음)
SAVE_DIR = paths.REPORTS_DATA_DIR
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

# ⚠️ [설정] 본인의 이메일과 '앱 비밀번호' 입력
IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = "zedd1324@gmail.com"
EMAIL_PASS = "yqvnhciedwuehkqz" # 띄어쓰기 없이 입력

# 감시할 발신자 키워드 (보낸 사람 이름이나 이메일에 포함된 단어)
TARGET_SENDERS = [
    "StockTwits",
    "McKinsey",
    "Seeking Alpha",
    "Morgan Stanley",
    "Goldman Sachs"
]

def clean_text(text):
    """특수문자 및 공백 정리"""
    return " ".join(text.split())

def decode_mime_words(s):
    """깨진 한글/특수문자 제목 디코딩"""
    if not s: return ""
    return "".join(
        (word.decode(encoding or "utf-8") if isinstance(word, bytes) else word)
        for word, encoding in decode_header(s)
    )

def collect_emails():
    print("📧 중요 이메일(투자 레터) 수집 중...")
    
    try:
        # 1. 지메일 접속
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("INBOX") # 받은편지함 선택

        report_content = [f"[Email Intelligence Briefing - {datetime.date.today()}]"]
        found_count = 0

        # 2. 타겟 발신자별 검색
        for target in TARGET_SENDERS:
            # 보낸 사람(FROM)에 target 키워드가 포함된 메일 검색
            status, messages = mail.search(None, f'(FROM "{target}")')
            
            if status != "OK" or not messages[0]:
                continue

            # 최신 메일 2개만 가져오기
            latest_ids = messages[0].split()[-2:]
            
            for num in reversed(latest_ids):
                try:
                    res, msg_data = mail.fetch(num, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # 제목 추출
                            subject = decode_mime_words(msg["Subject"])
                            sender = decode_mime_words(msg["From"])
                            
                            # 본문 추출 (HTML 태그 제거하고 텍스트만)
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode()

                            # 요약 정리
                            summary = f"\n### 📩 From: {sender}\n**Subject:** {subject}\n**Content Snippet:** {clean_text(body)[:500]}..."
                            report_content.append(summary)
                            found_count += 1
                            print(f"   ✅ [수집] {target}: {subject[:30]}...")
                except Exception as e:
                    print(f"   ⚠️ 메일 파싱 에러: {e}")
                    continue

        mail.logout()

        # 3. 저장
        if found_count > 0:
            save_path = os.path.join(SAVE_DIR, "email_briefing.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_content))
            print(f"🎉 총 {found_count}건의 투자 메일을 리포트로 저장했습니다.")
        else:
            print("☁️ 새로운 투자 메일이 없습니다.")

    except Exception as e:
        print(f"❌ 이메일 접속 실패 (앱 비밀번호 확인 필요): {e}")

if __name__ == "__main__":
    collect_emails()