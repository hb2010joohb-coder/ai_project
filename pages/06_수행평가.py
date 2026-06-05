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
    except Exception as e:
        return {"Aatrox": "아트록스", "LeeSin": "리 신", "Ezreal": "이즈리얼"}

def get_puuid(game_name, tag_line):
    """Riot ID로 고유 ID(PUUID) 검색"""
    url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            if response.status_code in [401, 403]:
                st.sidebar.error("🔑 시스템 개발자 키가 만료되었습니다. 키를 갱신해주세요.")
            elif response.status_code == 404:
                st.sidebar.error("🔍 플레이어를 찾을 수 없습니다. 닉네임과 태그를 정확히 확인해주세요.")
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
    """게임별 상세 성적 가공"""
    headers = {"X-Riot-Token": RIOT_API_KEY}
    match_data = []
    
    champ_dict = get_champion_dict()
    
    progress_text = f"플레이어의 최근 {len(match_ids)}경기 기록을 심층 분석하는 중입니다..."
    progress_bar = st.progress(0, text=progress_text)
    
    for idx, match_id in enumerate(match_ids):
        url = f"https://{ACCOUNT_ROUTE}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            info = resp.json().get('info', {})
            for participant in info.get('participants', []):
                if participant['puuid'] == target_puuid:
                    raw_role = participant.get('teamPosition', '')
                    if not raw_role or raw_role == 'UNKNOWN':
                        raw_role = participant.get('individualPosition', 'UNKNOWN')
                    
                    raw_role = str(raw_role).upper().strip()
                    if raw_role == 'UTILITY': raw_role = 'SUPPORT'
                    
                    if raw_role in ['', 'UNKNOWN', 'INDIVIDUAL', 'NONE']:
                        continue
                    
                    role_ko = ROLE_TRANSLATION.get(raw_role, f"{raw_role} (기타 라인)")
                    eng_champ_name = participant['championName']
                    kor_champ_name = champ_dict.get(eng_champ_name, champ_dict.get(eng_champ_name.lower(), eng_champ_name))
                    
                    match_data.append({
                        "win": "승리" if participant['win'] else "패배",
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

# --- 화면 구성 ---
st.set_page_config(page_title="LoL 프로파일러 대시보드", layout="wide")

st.title("📊 LoL 데이터 프로파일러 2.0")
st.caption("어려운 게임 지표를 직관적인 분석 보고서로 변환해 주는 맞춤형 전적 검색기입니다.")

with st.expander("💡 초보자를 위한 핵심 지표 이해하기", expanded=False):
    st.markdown("""
    * **종합 승률**: 최근 경기 중 승리한 비율입니다. **53% 이상**이면 현재 실력이 급상승 중이라는 지표입니다.
    * **전투 효율 (KDA)**: 적을 처치하거나 도운 총합을 내가 탈락한 횟수로 나눈 수치입니다. **3.0 이상**이면 매 경기 밥값을 톡톡히 하는 플레이어입니다.
    * **성향 태그**: 최근 데이터를 기반으로 AI가 판단한 이 유저의 고유 플레이 스타일입니다.
    """)

# 사이드바
st.sidebar.header("👤 플레이어 라이엇 ID")
game_name = st.sidebar.text_input("닉네임", placeholder="예: Hide on bush")
tag_line = st.sidebar.text_input("태그", placeholder="예: KR1")
match_count = st.sidebar.slider("분석 범위 설정 (최대 100판)", min_value=5, max_value=100, value=20, step=5)

if st.sidebar.button("실력 프로파일링 시작", type="primary"):
    if not game_name or not tag_line:
        st.error("닉네임과 태그를 입력해 주세요.")
    else:
        with st.spinner("라이엇 빅데이터 분석 엔진 가동 중..."):
            puuid = get_puuid(game_name, tag_line)
            
            if puuid:
                match_ids = get_match_ids(puuid, count=match_count)
                
                if not match_ids:
                    st.warning("분석할 최근 게임 기록이 존재하지 않습니다.")
                else:
                    df = get_match_details(match_ids, puuid)
                    
                    if df.empty:
                        st.error("정규 포지션 데이터가 부족합니다. (최근에 특수 모드만 즐겼는지 확인해 주세요.)")
                    else:
                        # 데이터 연산
                        total_games = len(df)
                        wins = df['win_bool'].sum()
                        losses = total_games - wins
                        win_rate = (wins / total_games) * 100
                        
                        avg_k = df['kills'].mean()
                        avg_d = df['deaths'].mean()
                        avg_a = df['assists'].mean()
                        kda = (avg_k + avg_a) / avg_d if avg_d != 0 else (avg_k + avg_a)
                        
                        # ✨ [업그레이드 1: 스타일 성향 분석 자동 태그 부여]
                        user_tags = []
                        if avg_k >= 7: user_tags.append("🎯 폭발적인 학살자")
                        elif avg_d <= 4: user_tags.append("🛡️ 철벽의 생존왕")
                        if avg_a >= 9: user_tags.append("🤝 신뢰받는 최고의 조력자")
                        if win_rate >= 55: user_tags.append("🔥 승리 청부사")
                        if not user_tags: user_tags.append("🏃 묵묵한 노력파 플레이어")
                        
                        # UI 출력
                        st.markdown(f"## 💎 **{game_name} #{tag_line}** 분석 리포트")
                        
                        # 태그 노출
                        tag_html = " ".join([f"<span style='background-color:#1e3d59; color:white; padding:5px 10px; border-radius:15px; font-weight:bold; margin-right:5px;'>{t}</span>" for t in user_tags])
                        st.markdown(f"**플레이어 성향:** {tag_html}", unsafe_allow_html=True)
                        st.write("")
                        
                        # 3단 카드 세련되게 배치
                        col1, col2, col3 = st.columns(3)
                        col1.metric("📊 종합 승률", f"{win_rate:.1f}%", f"{wins}승 {losses}패")
                        
                        kda_status = "👑 에이스 평가" if kda >= 3.5 else ("🏃 평범함" if kda >= 2.0 else "📉 침체기")
                        col2.metric("⚔️ 평균 전투 점수 (KDA)", f"{kda:.2f}", f"평균 {avg_k:.1f}킬 / {avg_d:.1f}데스 / {avg_a:.1f}어시")
                        
                        # 포지션 연산
                        role_stats = df.groupby('role').agg(판수=('win_bool', 'count'), 승리=('win_bool', 'sum')).reset_index()
                        role_stats['승률'] = (role_stats['승리'] / role_stats['판수']) * 100
                        
                        min_match_limit = 5 if total_games >= 50 else 2
                        reliable_roles = role_stats[role_stats['판수'] >= min_match_limit]
                        best_role = reliable_roles.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role'] if not reliable_roles.empty else role_stats.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role']
                        
                        col3.metric("🔥 주력 에이스 라인", best_role.split(" (")[0], f"승률 우수 포지션")
                        
                        # ✨ [업그레이드 2: 최근 매치 승/패 흐름 타일맵]
                        st.markdown("---")
                        st.write("### 🗂️ 최근 경기 승/패 타일맵")
                        st.caption("왼쪽에서 오른쪽으로 갈수록 최근에 진행한 게임입니다. (초록: 승리 / 빨강: 패배)")
                        
                        tile_cols = st.columns(min(total_games, 20)) # 최대 20개씩 끊어서 보여주기
                        for i, row in df.head(20).iterrows():
                            with tile_cols[i % 20]:
                                color = "#2ecc71" if row['win_bool'] else "#e74c3c"
                                st.markdown(f"<div style='background-color:{color}; color:white; text-align:center; padding:10px 0px; border-radius:5px; font-weight:bold; font-size:12px;'>{row['win']}</div>", unsafe_allow_html=True)
                        
                        # 시각화 그래프
                        st.markdown("---")
                        col_left, col_right = st.columns(2)
                        
                        with col_left:
                            st.write("### 🧭 라인별 플레이 비중")
                            fig_pie = px.pie(df, names='role', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
                            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                        with col_right:
                            st.write("### 📈 라인별 실제 승률")
                            fig_bar = px.bar(role_stats, x='role', y='승률', text=role_stats['승률'].apply(lambda x: f"{x:.1f}%"),
                                             labels={'승률': '승률 (%)', 'role': '포지션'},
                                             color='승률', color_continuous_scale='Viridis')
                            fig_bar.update_yaxes(range=[0, 100])
                            st.plotly_chart(fig_bar, use_container_width=True)
                            
                        st.markdown("---")
                        
                        # 모스트 캐릭터 목록
                        st.write("### 🏆 가장 손에 익은 선호 캐릭터(챔피언)")
                        champ_counts = df['champion'].value_counts().reset_index()
                        champ_counts.columns = ['캐릭터 이름 👤', '선택 횟수 (판)']
                        st.dataframe(champ_counts, use_container_width=True, hide_index=True)
