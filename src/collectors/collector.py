import requests
import json
import time
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Project root:", project_root)
print("sys.path:", sys.path)


from src.config import paths

# --- [1] 설정 ---
SAVE_DIR = paths.NEWS_DATA_DIR

# --- [2] 필터링 함수 (Gatekeeper - 수정됨) ---
def should_collect(news_item):
    """
    뉴스를 수집할지 말지 결정하는 함수.
    True를 반환하면 수집, False면 건너뜀.
    """
    title = news_item.get('title', '').lower() # 소문자로 변환하여 비교
    
    # [수정 1] ADMIN 체크 삭제 (유저가 올린 양질의 뉴스도 수집하기 위해)
    # if news_item.get('author_role') != 'ADMIN': ... (삭제됨)

    # [수정 2] 노이즈 키워드 강화 (한국어 + 영어)
    # 로그에 보였던 '(카더라)' 같은 찌라시나 가십성 키워드를 제외합니다.
    noise_keywords = [
        # 1. 신뢰도 낮은 정보
        "찌라시", "루머", "rumor",
        
        # 2. 연예/가십 (투자와 무관한)
        "열애", "결별", "dating", "scandal", "폭로", "충격",
        
        # 3. 스포츠 (단, 비즈니스 뉴스는 제외되도록 주의)
        "경기 결과", "match result", "highlight"
    ]
    
    # 제목에 노이즈 키워드가 있는지 확인
    for keyword in noise_keywords:
        if keyword in title:
            print(f"   🗑️ 패스 (노이즈/가십): {news_item['title']}")
            return False
            
    # [옵션] 제목이 너무 짧으면(5글자 미만) 패스 (ex: "대박", "속보")
    if len(news_item.get('title', '')) < 5:
        print(f"   📏 패스 (제목 너무 짧음): {news_item['title']}")
        return False

    return True

# --- [3] 메인 수집 로직 ---
def run_collector():
    # 1. 뉴스 리스트 요청 (최신 20개)
    list_url = "https://api.saveticker.com/api/news/list?page=1&page_size=20&sort=created_at_desc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("📡 최신 뉴스 리스트 스캔 중... (필터 완화됨)")
    try:
        response = requests.get(list_url, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    if response.status_code != 200:
        print("❌ 리스트 가져오기 실패")
        return

    news_list = response.json().get('news_list', [])
    
    count = 0
    for news_item in news_list:
        news_id = news_item['id']
        title = news_item['title']
        
        # 2. 필터링 (수집 가치 판단)
        if not should_collect(news_item):
            continue 

        # 3. 중복 확인
        filename = SAVE_DIR / f"{news_id}.json"
        if os.path.exists(filename):
            print(f"   ⏭️ 이미 있음: {title}")
            continue

        # 4. 상세 내용 수집
        detail_url = f"https://api.saveticker.com/api/news/detail/{news_id}"
        try:
            detail_res = requests.get(detail_url, headers=headers, timeout=5)
            
            if detail_res.status_code == 200:
                full_data = detail_res.json().get('news', {})
                
                # 본문 추출
                content_text = ""
                raw_content = full_data.get('content', '')
                
                if isinstance(raw_content, list):
                    content_text = "\n".join([c.get('content', '') for c in raw_content if c.get('type') == 'text'])
                else:
                    content_text = str(raw_content)

                # 데이터 구조핑
                save_data = {
                    "id": news_id,
                    "title": full_data.get('title', ''),
                    "created_at": full_data.get('created_at', ''),
                    "content": content_text,
                    "source": full_data.get('source', ''),
                    "tags": [t.get('name') for t in full_data.get('tags', [])],
                    "author": full_data.get('author_name', 'Unknown') # 작성자 정보 추가
                }

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=4)
                
                print(f"   ✅ 수집 완료: {title}")
                count += 1
                time.sleep(0.3) 
        except Exception as e:
            print(f"   ⚠️ 상세 수집 중 에러: {title} ({e})")
            continue
        
    print(f"\n🎉 총 {count}개의 뉴스를 새로 저장했습니다.")

if __name__ == "__main__":
    run_collector()