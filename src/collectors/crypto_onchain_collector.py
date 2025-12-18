import requests
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)
from src.config import paths
SAVE_DIR = paths.ASSET_DATA_DIR
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

def collect_defi_yields():
    print("⛓️ 크립토 온체인 데이터(DefiLlama) 수집 중...")
    
    # 스테이블코인 풀 수익률 조회 (예: Aave, Compound)
    # DefiLlama Yields API 사용
    url = "https://yields.llama.fi/pools"
    
    try:
        res = requests.get(url).json()
        data = res['data']
        
        # TVL 100M 이상, Stablecoin 필터링
        high_tvl_pools = [p for p in data if p['tvlUsd'] > 100000000 and p['stablecoin']]
        # 수익률(APY) 높은 순 정렬
        top_pools = sorted(high_tvl_pools, key=lambda x: x['apy'], reverse=True)[:5]
        
        lines = []
        for p in top_pools:
            lines.append(f"- {p['project']} ({p['symbol']}): APY {p['apy']:.2f}% (TVL: ${p['tvlUsd']/1000000:.0f}M)")
            
        content = "[Major Stablecoin Yields (Low Risk)]\n" + "\n".join(lines)
        
        with open(f"{SAVE_DIR}/crypto_yields.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 온체인 데이터 저장 완료.")
        
    except Exception as e:
        print(f"⚠️ 온체인 수집 실패: {e}")

if __name__ == "__main__":
    collect_defi_yields()