import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- 설정 및 API 키 (본인의 API Key를 입력하세요) ---
RIOT_API_KEY = "YOUR_RIOT_API_KEY_HERE" 

# 지역 설정 (한국 기준)
ACCOUNT_ROUTE = "asia"
GAME_ROUTE = "kr"

def get_puuid(game_name, tag_line):
    """Riot ID로 유저의 고유 ID(PUUID)를 가져옵니다."""
    url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/riot/account/v1/accounts/by-game-name/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['puuid']
    return None

def get_match_ids(puuid, count=20):
    """최근 매치 ID 리스트를 가져옵니다."""
    url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_match_details(match_ids, target_puuid):
    """매치 상세 정보에서 사용자의 승패 및 포지션 데이터를 추출합니다."""
    headers = {"X-Riot-Token": RIOT_API_KEY}
    match_data = []
    
    # 스트림릿 프로그레스 바 적용
    progress_bar = st.progress(0)
    for idx, match_id in enumerate(match_ids):
        url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            info = resp.json().get('info', {})
            # 참가자 중 target_puuid 찾기
            for participant in info.get('participants', []):
                if participant['puuid'] == target_puuid:
                    # 포지션 매핑 정제 (UTILITY -> SUPPORT)
                    role = participant.get('teamPosition', 'UNKNOWN')
                    if role == 'UTILITY': role = 'SUPPORT'
                    if role == '': role = 'UNKNOWN'
                    
                    match_data.append({
                        "win": participant['win'],
                        "role": role,
                        "kills": participant['kills'],
                        "deaths": participant['deaths'],
                        "assists": participant['assists'],
                        "champion": participant['championName']
                    })
        progress_bar.progress((idx + 1) / len(match_ids))
    progress_bar.empty()
    return pd.DataFrame(match_data)

# --- 스트림릿 UI 레이아웃 ---
st.set_page_config(page_title="LoL 전적 및 포지션 분석기", layout="wide")
st.title("🎮 LoL 전적 및 포지션 분석 대시보드")
st.caption("Riot API와 Streamlit을 이용한 실시간 유저 데이터 분석")

# 사이드바 검색창
st.sidebar.header("🔍 플레이어 검색")
game_name = st.sidebar.text_input("Riot ID (닉네임)", placeholder="예: Hide on bush")
tag_line = st.sidebar.text_input("Tagline (태그)", placeholder="예: KR1")
match_count = st.sidebar.slider("분석할 판 수", 5, 30, 10)

if st.sidebar.button("전적 검색"):
    if not game_name or not tag_line:
        st.error("닉네임과 태그를 모두 입력해주세요.")
    elif RIOT_API_KEY == "YOUR_RIOT_API_KEY_HERE":
        st.warning("코드 내부의 RIOT_API_KEY를 실제 키로 변경해주세요.")
    else:
        with st.spinner("라이엇 서버에서 데이터를 불러오는 중..."):
            puuid = get_puuid(game_name, tag_line)
            
            if not puuid:
                st.error("플레이어를 찾을 수 없습니다. 닉네임과 태그를 다시 확인하세요.")
            else:
                match_ids = get_match_ids(puuid, count=match_count)
                
                if not match_ids:
                    st.warning("최근 진행한 게임이 없습니다.")
                else:
                    df = get_match_details(match_ids, puuid)
                    
                    if df.empty:
                        st.error("매치 상세 정보를 가져오는데 실패했습니다.")
                    else:
                        # --- 데이터 연산 ---
                        total_games = len(df)
                        wins = df['win'].sum()
                        losses = total_games - wins
                        win_rate = (wins / total_games) * 100
                        
                        avg_k = df['kills'].mean()
                        avg_d = df['deaths'].mean()
                        avg_a = df['assists'].mean()
                        kda = (avg_k + avg_a) / avg_d if avg_d != 0 else (avg_k + avg_a)
                        
                        # --- 화면 출력 ---
                        st.subheader(f"✨ {game_name} #{tag_line} 님의 최근 {total_games}경기 분석")
                        
                        # 메트릭 대시보드 (기본 통계)
                        col1, col2, col3 = st.columns(3)
                        col1.metric("종합 승률", f"{win_rate:.1f}%", f"{wins}승 {losses}패")
                        col2.metric("평균 KDA", f"{kda:.2f}:1", f"{avg_k:.1f} / {avg_d:.1f} / {avg_a:.1f}")
                        
                        # 포지션 추천 알고리즘 (가장 승률이 높은 포지션 선정)
                        role_stats = df.groupby('role').agg(
                            판수=('win', 'count'),
                            승리=('win', 'sum')
                        ).reset_index()
                        role_stats['승률'] = (role_stats['승리'] / role_stats['판수']) * 100
                        
                        # UNKNOWN 제외하고 모스트 포지션 추천
                        valid_roles = role_stats[role_stats['role'] != 'UNKNOWN']
                        if not valid_roles.empty:
                            best_role = valid_roles.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role']
                            col3.metric("🔥 추천 포지션", best_role, "최근 승률 기준 베스트")
                        else:
                            col3.metric("🔥 추천 포지션", "데이터 부족")
                        
                        st.markdown("---")
                        
                        # 시각화 섹션
                        col_left, col_right = st.columns(2)
                        
                        with col_left:
                            st.write("### 🧭 포지션 플레이 비율")
                            fig_pie = px.pie(df, names='role', title="최근 포지션 분포", hole=0.4,
                                             color_discrete_sequence=px.colors.sequential.RdBu)
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                        with col_right:
                            st.write("### 📊 포지션별 승률 통계")
                            fig_bar = px.bar(role_stats, x='role', y='승률', text=role_stats['승률'].apply(lambda x: f"{x:.1f}%"),
                                             title="포지션별 승률 (%)", labels={'승률': '승률 (%)', 'role': '라인'},
                                             color='승률', color_continuous_scale='Blues')
                            st.plotly_chart(fig_bar, use_container_width=True)
                            
                        # 최근 플레이한 챔피언 순위
                        st.write("### 🏆 최근 모스트 챔피언")
                        champ_counts = df['champion'].value_counts().reset_index()
                        champ_counts.columns = ['챔피언', '판수']
                        st.dataframe(champ_counts, use_container_width=True)
