import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    """게임별 상세 성적 가공"""
    headers = {"X-Riot-Token": RIOT_API_KEY}
    match_data = []
    
    champ_dict = get_champion_dict()
    
    progress_text = f"플레이어의 최근 {len(match_ids)}경기 데이터 정밀 프로파일링 중..."
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
                        "champion": kor_champ_name,
                        "match_index": len(match_ids) - idx # 그래프 순서용 지표
                    })
        progress_bar.progress((idx + 1) / len(match_ids), text=progress_text)
    progress_bar.empty()
    return pd.DataFrame(match_data)

# --- 화면 구성 ---
st.set_page_config(page_title="LoL AI 빅데이터 프로파일러", layout="wide")

st.title("🚀 LoL AI 빅데이터 프로파일러 3.0")
st.caption("고도화된 매치 트래킹 기술을 통해 플레이어의 숨겨진 실력과 전투 기복을 정밀 분석합니다.")

with st.expander("💡 롤알못을 위한 가이드북", expanded=False):
    st.markdown("""
    * **플레이어 성향**: 유저의 플레이 스타일(공격 지향형, 안정 추구형 등)을 종합하여 AI가 부여한 성격 가이드입니다.
    * **KDA (전투 효율)**: (킬 + 어시스트) ÷ 데스. 수치가 높을수록 훌륭하며, **3.5를 넘어가면 해당 구간 최고의 에이스**입니다.
    * **승/패 타일맵**: 최근 경기 결과를 바둑판처럼 나열한 것입니다. 연속된 색상을 통해 최근 컨디션 흐름을 볼 수 있습니다.
    """)

# 사이드바
st.sidebar.header("🔍 대상 플레이어 입력")
game_name = st.sidebar.text_input("닉네임", placeholder="예: Hide on bush")
tag_line = st.sidebar.text_input("태그", placeholder="예: KR1")
match_count = st.sidebar.slider("추적할 경기 수", min_value=5, max_value=100, value=20, step=5)

if st.sidebar.button("실력 정밀 프로파일링 시작", type="primary"):
    if not game_name or not tag_line:
        st.error("닉네임과 태그를 빈칸 없이 입력해 주세요.")
    else:
        with st.spinner("라이엇 빅데이터 연산 엔진 작동 중..."):
            puuid = get_puuid(game_name, tag_line)
            
            if puuid:
                match_ids = get_match_ids(puuid, count=match_count)
                
                if not match_ids:
                    st.warning("조회 가능한 최근 매치 기록이 없습니다.")
                else:
                    df = get_match_details(match_ids, puuid)
                    
                    if df.empty:
                        st.error("최근 정규 포지션 데이터가 부족합니다. 칼바람 나락이 아닌 '소환사의 협곡' 플레이 내역을 확인해 주세요.")
                    else:
                        # 기본 데이터 연산
                        total_games = len(df)
                        wins = df['win_bool'].sum()
                        losses = total_games - wins
                        win_rate = (wins / total_games) * 100
                        
                        avg_k = df['kills'].mean()
                        avg_d = df['deaths'].mean()
                        avg_a = df['assists'].mean()
                        kda = (avg_k + avg_a) / avg_d if avg_d != 0 else (avg_k + avg_a)
                        
                        # AI 성향 분석 태그
                        user_tags = []
                        if avg_k >= 7: user_tags.append("🎯 폭발적인 학살자")
                        elif avg_d <= 4: user_tags.append("🛡️ 철벽의 생존왕")
                        if avg_a >= 9: user_tags.append("🤝 신뢰받는 조력자")
                        if win_rate >= 55: user_tags.append("🔥 승리 청부사")
                        if not user_tags: user_tags.append("🏃 묵묵한 노력파")
                        
                        # 상단 분석 리포트 제목
                        st.markdown(f"## 💎 **{game_name} #{tag_line}** 님의 종합 실력 검증")
                        
                        tag_html = " ".join([f"<span style='background-color:#0f2027; color:#203a43; background: linear-gradient(to right, #2c5364, #203a43, #0f2027); color:white; padding:6px 14px; border-radius:20px; font-weight:bold; margin-right:6px; font-size:13px;'>{t}</span>" for t in user_tags])
                        st.markdown(f"**전투 성향:** {tag_html}", unsafe_allow_html=True)
                        st.write("")
                        
                        # 주요 요약 카드 배치
                        col1, col2, col3 = st.columns(3)
                        col1.metric("📊 종합 승률", f"{win_rate:.1f}%", f"{wins}승 {losses}패")
                        
                        # KDA 세부 매칭 문구
                        kda_eval = "👑 최고 존엄 에이스" if kda >= 3.5 else ("🏃 자기 몫 해내는 중" if kda >= 2.0 else "📉 현재 집중력 저하 상태")
                        col2.metric("⚔️ 평균 전투 점수 (KDA)", f"{kda:.2f}", f"{avg_k:.1f} / {avg_d:.1f} / {avg_a:.1f} ({kda_eval})")
                        
                        # 포지션 연산
                        role_stats = df.groupby('role').agg(판수=('win_bool', 'count'), 승리=('win_bool', 'sum')).reset_index()
                        role_stats['승률'] = (role_stats['승리'] / role_stats['판수']) * 100
                        
                        min_limit = 5 if total_games >= 50 else 2
                        reliable_roles = role_stats[role_stats['판수'] >= min_limit]
                        best_role = reliable_roles.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role'] if not reliable_roles.empty else role_stats.sort_values(by=['승률', '판수'], ascending=False).iloc[0]['role']
                        
                        col3.metric("🔥 주력 캐리 라인", best_role.split(" (")[0], "가장 최적화된 포지션")
                        
                        # 승/패 타일맵 컨테이너 구조화
                        st.markdown("---")
                        st.write("### 🗂️ 최근 매치 컨디션 맵")
                        st.caption("최근 경기 순서대로 정렬된 타일입니다. 색상이 한쪽으로 치우쳐 있다면 연승 혹은 연패 중임을 의미합니다.")
                        
                        tile_cols = st.columns(min(total_games, 20))
                        for i, row in df.head(20).iterrows():
                            with tile_cols[i % 20]:
                                bg_color = "#11998e" if row['win_bool'] else "#cb2d3e"
                                st.markdown(f"<div style='background-color:{bg_color}; color:white; text-align:center; padding:12px 4px; border-radius:6px; font-weight:bold; font-size:11px; box-shadow: 1px 1px 3px rgba(0,0,0,0.15);'>{row['win']}</div>", unsafe_allow_html=True)
                        
                        # ✨ [업그레이드 3.0 신규 지표 차트: 경기별 전투 변동 트렌드]
                        st.markdown("---")
                        st.write("### 📈 최근 경기별 실력 변동 그래프")
                        st.caption("경기를 거듭하며 기록한 킬(적 처치)과 데스(본인 탈락)의 추이 변화입니다. 두 선의 격차가 벌어질수록 활약한 경기입니다.")
                        
                        trend_df = df.iloc[::-1].reset_index() # 시간 순서대로 정렬 (과거 -> 현재)
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(x=trend_df.index+1, y=trend_df['kills'], mode='lines+markers', name='공격력 (Kill)', line=dict(color='#2196F3', width=3)))
                        fig_trend.add_trace(go.Scatter(x=trend_df.index+1, y=trend_df['deaths'], mode='lines+markers', name='탈락 횟수 (Death)', line=dict(color='#E91E63', width=2, dash='dash')))
                        fig_trend.update_layout(xaxis_title="진행한 경기 순서 (오른쪽이 최신)", yaxis_title="횟수", margin=dict(t=20, b=20, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig_trend, use_container_width=True)
                        
                        # 메인 파이/바 시각화 지표
                        st.markdown("---")
                        col_left, col_right = st.columns(2)
                        
                        with col_left:
                            st.write("### 🧭 포지션 선호도 분포")
                            fig_pie = px.pie(df, names='role', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                        with col_right:
                            st.write("### 📊 라인별 실제 승리 지동표")
                            fig_bar = px.bar(role_stats, x='role', y='승률', text=role_stats['승률'].apply(lambda x: f"{x:.1f}%"),
                                             labels={'승률': '승률 (%)', 'role': '포지션 위치'},
                                             color='승률', color_continuous_scale='Cividis')
                            fig_bar.update_yaxes(range=[0, 100])
                            st.plotly_chart(fig_bar, use_container_width=True)
                            
                        st.markdown("---")
                        
                        # 최다 선호 캐릭터 TOP 랭킹
                        st.write("### 🏆 가장 자신 있는 시그니처 캐릭터 (챔피언 선호 랭킹)")
                        champ_counts = df['champion'].value_counts().reset_index()
                        champ_counts.columns = ['캐릭터 이름 👤', '선택 및 플레이 횟수 (판)']
                        st.dataframe(champ_counts, use_container_width=True, hide_index=True)
