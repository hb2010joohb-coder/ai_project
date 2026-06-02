import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(page_title="GG.Streamlit - 게임 전적 검색", layout="wide", page_icon="🎮")

# 가상 데이터 생성 함수 (실제 구현 시 API 연동 부분)
def get_mock_data(nickname):
    if not nickname:
        return None
    # 랜덤하지만 그럴듯한 데이터 생성
    np.random.seed(len(nickname)) 
    win_rate = np.random.uniform(45, 65)
    games_played = np.random.randint(50, 200)
    wins = int(games_played * (win_rate / 100))
    losses = games_played - wins
    
    # 최근 10경기 데이터
    recent_games = pd.DataFrame({
        '치른 시간': [f"{i}일 전" for i in range(1, 11)],
        '결과': np.random.choice(['승리', '패배'], size=10, p=[win_rate/100, 1 - win_rate/100]),
        'K': np.random.randint(1, 15, size=10),
        'D': np.random.randint(1, 12, size=10),
        'A': np.random.randint(2, 20, size=10),
        '플레이한 캐릭터': np.random.choice(['캐릭터A', '캐릭터B', '캐릭터C'], size=10)
    })
    recent_games['KDA'] = ((recent_games['K'] + recent_games['A']) / np.where(recent_games['D'] == 0, 1, recent_games['D'])).round(2)
    
    return {
        'nickname': nickname,
        'win_rate': round(win_rate, 1),
        'wins': wins,
        'losses': losses,
        'total': games_played,
        'recent': recent_games
    }

# 2. 상단 타이틀 및 검색 바
st.title("🎮 GG.Streamlit")
st.subheader("게임 닉네임을 입력하여 플레이 통계와 승률을 분석해보세요.")

# 검색창을 사이드바 또는 메인 화면에 배치
nickname = st.text_input("게임 닉네임을 입력하세요 (예: 길동이#KR1)", placeholder="닉네임#태그")

if nickname:
    data = get_mock_data(nickname)
    
    # --- 3. 대시보드 레이아웃 구성 ---
    st.markdown(f"## 👤 {data['nickname']} 님의 분석 리포트")
    st.divider()
    
    # 핵심 지표 (Metrics) - 3열 배치
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="총 판수", value=f"{data['total']}전")
    with col2:
        st.metric(label="종합 승률", value=f"{data['win_rate']}%", delta=f"{data['wins']}승 {data['losses']}패")
    with col3:
        avg_kda = data['recent']['KDA'].mean().round(2)
        st.metric(label="최근 10경기 평균 KDA", value=f"{avg_kda} : 1")
        
    st.divider()
    
    # 시각화 섹션 - 2열 배치
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 승/패 비율")
        # 파이 차트 그리기
        fig_pie = px.pie(
            values=[data['wins'], data['losses']], 
            names=['승리', '패배'], 
            color=['승리', '패배'],
            color_discrete_map={'승리': '#2563EB', '패배': '#DC2626'},
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_right:
        st.subheader("📈 최근 10경기 KDA 추이")
        # 선 그래프 그리기
        fig_line = px.line(
            data['recent'].iloc[::-1], # 최근 경기가 오른쪽으로 가도록 뒤집기
            x='치른 시간', 
            y='KDA', 
            markers=True,
            title="경기별 KDA 변화"
        )
        fig_line.update_traces(line_color='#059669')
        st.plotly_chart(fig_line, use_container_width=True)
        
    st.divider()
    
    # 4. 상세 전적 테이블 및 분석 평가
    st.subheader("📋 최근 10경기 상세 기록")
    
    # 조건부 스타일링 (승리는 파란색 배경, 패배는 빨간색 배경 느낌 주기)
    def style_result(val):
        color = '#E0F2FE' if val == '승리' else '#FEE2E2'
        return f'background-color: {color}'
    
    st.dataframe(
        data['recent'].style.applymap(style_result, subset=['결과']),
        use_container_width=True
    )
    
    # AI/룰 기반 간단한 게임 분석 코멘트
    st.subheader("🧠 종합 게임 플레이 분석")
    if data['win_rate'] >= 55:
        st.success("🎯 **현재 티어 상승의 적기입니다!** 승률이 매우 높으며 전반적인 캐리력이 돋보입니다.")
    elif data['win_rate'] >= 48:
        st.info("⚖️ **안정적인 숙련도를 보여주고 있습니다.** 몇 판의 아쉬운 패배만 줄이면 한 단계 더 성장할 수 있습니다.")
    else:
        st.warning("⚠️ **팀원과의 호흡이나 챔피언 폭 조절이 필요해보입니다.** 최근 데스(Death) 관리에 조금 더 신경 써보세요!")

else:
    # 닉네임 입력 전 홈 화면 가이드
    st.info("👆 상단 검색창에 게임 닉네임을 입력하고 Enter를 누르면 분석이 시작됩니다.")
