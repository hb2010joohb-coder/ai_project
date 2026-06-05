import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- 라이엇 API 키 설정 ---
if "riot_api_key" in st.secrets:
    RIOT_API_KEY = st.secrets["riot_api_key"]
else:
    st.sidebar.error("🚨 시스템 설정 오류: API 키를 찾을 수 없습니다.")
    st.stop()

ACCOUNT_ROUTE = "asia"

# 영문 포지션을 한글로 변환하는 사전 (대문자 기준)
ROLE_TRANSLATION = {
    'TOP': '탑 (상단 라인 ⚔️)',
    'JUNGLE': '정글 (사냥꾼 🌲)',
    'MIDDLE': '미드 (중앙 라인 🔮)',
    'MID': '미드 (중앙 라인 🔮)',       # 💡 혹시 모를 축약형 대비 추가
    'BOTTOM': '원딜 (원거리 공격수 🎯)',
    'SUPPORT': '서포터 (아군 지원 🛡️)'
}

@st.cache_data
def get_champion_dict():
    """라이엇 데이터 드래곤에서 영문 챔피언 이름을 한국어 이름으로 바꾸는 사전을 가져옵니다."""
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
    except Exception as e:
        return {"Aatrox": "아트록스", "LeeSin": "리 신", "Ezreal": "이즈리얼"}

def get_puuid(game_name, tag_line):
    """Riot ID로 유저의 고유 ID(PUUID)를 검색"""
    url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            if response.status_code in [401, 403]:
                st.sidebar.error("🔑 시스템 개발자 키가 만료되었습니다. 키를 갱신해주세요.")
            elif response.status_code == 404:
                st.sidebar.error("🔍 플레이어를 찾을 수 없습니다. 닉네임과 태그를 정확히 입력했는지 확인해주세요.")
            else:
                st.sidebar.error(f"서버 오류 발생 (코드: {response.status_code})")
            return None
        return response.json()['puuid']
    except Exception as e:
        st.sidebar.error(f"통신 실패: {e}")
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
    """게임별 상세 성적 추출 및 초보자용 가이드 가공"""
    headers = {"X-Riot-Token": RIOT_API_KEY}
    match_data = []
    
    champ_dict = get_champion_dict()
    
    progress_text = "플레이어의 최근 경기 기록을 분석하는 중입니다..."
    progress_bar = st.progress(0, text=progress_text)
    
    for idx, match_id in enumerate(match_ids):
        url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            info = resp.json().get('info', {})
            for participant in info.get('participants', []):
                if participant['puuid'] == target_puuid:
                    # 💡 대소문자 꼬임 방지를 위해 upper()로 강제 대문자 변환
                    raw_role = str(participant.get('teamPosition', 'UNKNOWN')).upper().strip()
                    
                    if raw_role == 'UTILITY': raw_role = 'SUPPORT'
                    
                    # 칼바람 등 완전 무작위 모드에서 발생하는 무효 데이터만 스킵
                    if raw_role in ['', 'UNKNOWN', 'INDIVIDUAL', 'NONE']:
                        continue
                    
                    # 사전에 등록된 한글명이 있으면 바꾸고, 없으면 영문 그대로 노출해서 누락 방지
                    role_ko = ROLE_TRANSLATION.get(raw_role, f"{raw_role} (기타 라인)")
                    
                    eng_champ_name = participant['championName']
                    kor_champ_name = champ_dict.get(eng_champ_name, champ_dict.get(eng_champ_name.lower(), eng_champ_name))
                    
                    match_data.append({
                        "win": "승리 🎉" if participant['win'] else "패배 💧",
                        "win_bool": participant['win'],
                        "role": role_ko,
                        "kills": participant['kills'],
                        "deaths": participant['deaths'],
                        "assists": participant['assists'],
                        "champion": kor_champ_name
                    })
        progress_bar.progress((idx + 1) / len(match_ids), text=progress_text)
    progress_bar.empty()
    return pd.DataFrame(match_data)

# --- 스트림릿 웹 화면 구성 ---
st.set_page_config(page_title="누구나 보는 LoL 전적 분석기", layout="wide")

st.title("🎮 누구나 쉽게 보는 롤(LoL) 전적 대시보드")
st.caption("어려운 게임 용어 대신, 누구나 한눈에 플레이어의 실력을 파악할 수 있도록 도와주는 분석기입니다.")

with st.expander("💡 롤을 잘 모르시는 분들을 위한 용어 설명 가이드", expanded=False):
    st.markdown("""
    * **승률**: 전체 판 수 중 이긴 게임의 비율입니다. **50%를 넘으면 1인분 이상** 잘하고 있다는 뜻입니다.
    * **KDA (전투 효율)**: 내가 적을 쓰러뜨리거나(K) 도운 횟수(A)를 내가 쓰러진 횟수(D)로 나눈 점수입니다. 
      * 🟥 **2.0 미만**: 조금 힘겨운 경기를 펼치고 있어요.
      * 🟨 **2.0 ~ 3.5**: 자기 역할을 평범하게 잘 수행하고 있어요.
      * 🟩 **3.5 이상**: 팀을 승리로 이끄는 에이스(Ace) 역할을 하고 있어요!
    * **포지션(라인)**: 축구의 공격수, 미드필더, 수비수처럼 롤에도 5가지 역할 분담이 있습니다.
    """)

# 사이드바 입력창
st.sidebar.header("🔍 플레이어 검색")
st.sidebar.info("게임 안에서 보이는 '닉네임'과 '태그(#KR1 등)'를 따로 나누어 입력해주세요.")
game_name = st.sidebar.text_input("닉네임 (Riot ID)", placeholder="예: Hide on bush")
tag_line = st.sidebar.text_input("태그 (Tagline)", placeholder="예: KR1")
match_count = st.sidebar.slider("분석할 경기 수 (많을수록 정확해요)", 5, 20, 15)

if st.sidebar.button("실력 분석 시작"):
    if not game_name or not tag_line:
        st.error("닉네임과 태그를 모두 정확히 입력하셔야 분석이 가능합니다.")
    else:
        with st.spinner("라이엇 서버에서 데이터를 안전하게 가져오는 중..."):
            puuid = get_puuid(game_name, tag_line)
            
            if puuid:
                match_ids = get_match_ids(puuid, count=match_count)
                
                if not match_ids:
                    st.warning("최근에 진행한 게임 기록이 없는 플레이어입니다.")
                else:
                    df = get_match_details(match_ids, puuid)
                    
                    if df.empty:
                        st.error("분석할 수 있는 정규 라인전 기록이 부족합니다. 최근에 칼바람 나락 모드만 플레이했는지 확인해보세요.")
                    else:
                        # --- 데이터 계산 ---
                        total_games = len(df)
                        wins = df['win_bool'].sum()
                        losses = total_games - wins
                        win_rate = (wins / total_games) * 100
                        
                        avg_k = df['kills'].mean()
                        avg_d = df['deaths'].mean()
                        avg_a = df['assists'].mean()
                        kda = (avg_k + avg_a) / avg_d if avg_d != 0 else (avg_k + avg_a)
                        
                        if kda >= 3.5: kda_eval = "👑 매우 뛰어남 (팀의 에이스)"
                        elif kda >= 2.0: kda_eval = "🏃 준수함 (평균적인 활약)"
                        else: kda_eval = "📉 다소 아쉬움 (집중 수련 필요)"
                        
                        # --- 화면 결과 출력 ---
                        st.markdown(f"## ✨ **{game_name} #{tag_line}** 님의 실력 요약 보고서")
                        st.write(f"최근 진행한 정규 포지션 **{total_games}경기**를 바탕으로 분석한 결과입니다.")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("📊 종합 승률", f"{win_rate:.1f}%", f"{wins}번 이기고 {losses}번 짐")
                        col2.metric("⚔️ 전투 효율 (KDA)", f"{kda:.2f} 점", kda_eval)
                        
                        # 포지션별 통계 연산
                        role_stats = df.groupby('role').agg(
                            판수=('win_bool', 'count'),
                            승리=('win_bool', 'sum')
                        ).reset_index()
                        role_stats['승률'] = (role_stats['승리'] / role_stats['판수']) * 100
                        
                        # 추천 알고리즘 (최소 2판 이상 기준)
                        reliable_roles = role_stats[role_stats['판수'] >= 2]
                        
                        if not reliable_roles.empty:
                            best_role = reliable_roles.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role']
                            col3.metric("🔥 가장 자신 있는 포지션", best_role.split(" (")[0], "최소 2판 이상 수행 기준 베스트")
                        else:
                            best_role = role_stats.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role']
                            col3.metric("🔥 가장 자신 있는 포지션", best_role.split(" (")[0], "단판 플레이 기준 최고 승률")
                        
                        st.markdown("---")
                        
                        col_left, col_right = st.columns(2)
                        with col_left:
                            st.write("### 🧭 어떤 포지션을 주로 가나요?")
                            fig_pie = px.pie(df, names='role', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                        with col_right:
                            st.write("### 📈 각 포지션별 승률은 어떤가요?")
                            fig_bar = px.bar(role_stats, x='role', y='승률', text=role_stats['승률'].apply(lambda x: f"{x:.1f}%"),
                                             labels={'승률': '승리 확률 (%)', 'role': '포지션 위치'},
                                             color='승률', color_continuous_scale='YlGnBu')
                            fig_bar.update_yaxes(range=[0, 100])
                            st.plotly_chart(fig_bar, use_container_width=True)
                            
                        st.markdown("---")
                        
                        st.write("### 🏆 최근 가장 자주 선택한 캐릭터(챔피언)")
                        st.caption("플레이어가 어떤 캐릭터를 선호하는지 보여줍니다.")
                        champ_counts = df['champion'].value_counts().reset_index()
                        champ_counts.columns = ['캐릭터 이름 👤', '플레이 횟수 (판)']
                        st.dataframe(champ_counts, use_container_width=True, hide_index=True)
