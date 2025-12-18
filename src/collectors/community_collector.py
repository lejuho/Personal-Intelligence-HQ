import requests
import json
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)
# --- [설정] ---
from src.config import paths
SAVE_DIR = paths.COMMUNITY_DATA_DIR  # 별도 폴더에 저장
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- [필터링] ---
def should_collect(post_item):
    """커뮤니티 글 필터링 (노이즈 제거)"""
    title = post_item.get('title', '').lower()
    content = post_item.get('content', '').lower()
    
    # 1. 너무 짧은 글(잡담) 제외
    if len(content) < 30: 
        print(f"   🗑️ 패스 (너무 짧음): {post_item['title']}")
        return False

    # 2. 노이즈 키워드 필터링 (정치, 스포츠 등)
    noise_keywords = ["election", "vote", "soccer", "baseball"]
    check_text = title + " " + content
    for k in noise_keywords:
        if k in check_text:
            print(f"   🗑️ 패스 (노이즈): {post_item['title']}")
            return False
            
    return True

def run_community_collector():
    # 커뮤니티 API (카테고리: user_news)
    list_url = "https://api.saveticker.com/api/community/list?page=1&page_size=20&category=user_news&sort=created_at_desc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print("🗣️ 커뮤니티 여론(User News) 스캔 중...")
    try:
        response = requests.get(list_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ 리스트 실패 (Status: {response.status_code})")
            return

        # 커뮤니티 API의 키는 'posts' 입니다.
        posts = response.json().get('posts', [])
        
        count = 0
        for post in posts:
            post_id = post['id']
            title = post['title']
            
            # 1. 필터링
            if not should_collect(post):
                continue

            # 2. 중복 확인
            filename = os.path.join(SAVE_DIR, f"{post_id}.json")
            if os.path.exists(filename):
                continue # 조용히 넘어감

            # 3. 상세 내용 수집 (선택사항이나, 확실한 저장을 위해 호출)
            detail_url = f"https://api.saveticker.com/api/community/detail/{post_id}"
            detail_res = requests.get(detail_url, headers=headers)
            
            if detail_res.status_code == 200:
                # 상세 데이터 구조 확인 필요 (보통 'post' 키 안에 있음)
                full_data = detail_res.json().get('post', post) # 없으면 리스트 데이터 사용
                
                # 저장할 데이터 구조
                save_data = {
                    "id": post_id,
                    "title": full_data['title'],
                    "created_at": full_data['created_at'],
                    "content": full_data.get('content', ''),
                    "author": full_data.get('author_name', 'Unknown'),
                    "view_count": full_data.get('view_count', 0),
                    "likes": full_data.get('like_stats', {}).get('like_count', 0),
                    "source": "Saveticker Community"
                }

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=4)
                
                print(f"   ✅ 수집: {title}")
                count += 1
                time.sleep(0.5)

        if count > 0:
            print(f"🎉 총 {count}개의 커뮤니티 인사이트를 추가했습니다.")
        else:
            print("💤 새로운 커뮤니티 글이 없습니다.")

    except Exception as e:
        print(f"⚠️ 에러 발생: {e}")

if __name__ == "__main__":
    run_community_collector()