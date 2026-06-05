import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time  # 💡 429 오류 제어를 위한 시간 모듈 추가

# --- 라이엇 API 키 설정 ---
if "riot_api_key" in st.secrets:
    RIOT_API_KEY = st.secrets["riot_api_key"]
else:
    st.sidebar.error("🚨 시스템 설정 오류: API 키를 찾을 수 없습니다.")
    st.stop()

ACCOUNT_ROUTE = "asia"

# 영문 포지션을 한글로 변환하는 사전
ROLE_TRANSLATION = {
    'TOP': '탑 (상단 라인 ⚔️)',
    'JUNGLE': '정글 (사냥꾼 🌲)',
    'MIDDLE': '미드 (중앙 라인 🔮)',
    'MID': '미드 (중앙 라인 🔮)',
    'BOTTOM': '원딜 (원거리 공격수 🎯)',
    'SUPPORT': '서포터 (아군 지원 🛡️)'
}

@st.cache_data
def get_champion_dict():
    """라이엇 데이터 드래곤에서 최신 챔피언 한글 사전을 가져옵니다."""
    try:
        version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        latest_version = requests.get(version_url).json()[0]
        
        champ_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/ko_KR/champion.json"
        champ_data = requests.get(champ_url).json()['data']
        
        champ_dict = {}
        for champ_id, info in champ_data.items():
            champ_dict[champ_id] = info['name']
            champ_dict[champ_id.lower()] = info['name']
            
        return champ_dict
    except Exception:
        return {"Aatrox": "아트록스", "LeeSin": "리 신", "Ezreal": "이즈리얼"}

def get_puuid(game_name, tag_line):
    """Riot ID로 고유 ID(PUUID) 검색"""
    url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            st.sidebar.warning("⚠️ 서버 요청이 일시적으로 많습니다. 잠시 후 다시 시도해 주세요.")
            return None
        if response.status_code != 200:
            if response.status_code in [401, 403]:
                st.sidebar.error("🔑 시스템 개발자 키가 만료되었습니다. 키를 갱신해주세요.")
            elif response.status_code == 404:
                st.sidebar.error("🔍 플레이어를 찾을 수 없습니다. 닉네임과 태그를 정확히 입력해주세요.")
            else:
                st.sidebar.error(f"서버 오류 발생 (코드: {response.status_code})")
            return None
        return response.json()['puuid']
    except Exception:
        return None

def get_match_ids(puuid, count=20):
    """최근 게임 기록 ID 가져오기"""
    url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_match_details(match_ids, target_puuid):
    """게임별 상세 성적 가공 (429 요청 제한 우회 로직 내장)"""
    headers = {"X-Riot-Token": RIOT_API_KEY}
    match_data = []
    
    champ_dict = get_champion_dict()
    
    progress_bar = st.progress(0, text="플레이어의 최근 데이터를 분석하는 중...")
    
    idx = 0
    while idx < len(match_ids):
        match_id = match_ids[idx]
        url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        resp = requests.get(url, headers=headers)
        
        # 💡 [핵심 수정]: 429 과부하 오류 발생 시 3초 동안 대기 후 해당 경기 재요청
        if resp.status_code == 429:
            progress_bar.text(f"⏳ 라이엇 서버 요청 제한 규칙으로 인해 3초간 대기합니다... ({idx}/{len(match_ids)})")
            time.sleep(3.0)
            continue  # idx를 증가시키지 않고 동일한 경기 ID로 재시도
            
        if resp.status_code == 200:
            info = resp.json().get('info', {})
            for participant in info.get('participants', []):
                if participant['puuid'] == target_puuid:
                    raw_role = participant.get('teamPosition', '')
                    if not raw_role or raw_role == 'UNKNOWN':
                        raw_role = participant.get('individualPosition', 'UNKNOWN')
                    
                    raw_role = str(raw_role).upper().strip()
