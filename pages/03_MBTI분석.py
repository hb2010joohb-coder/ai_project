import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 레이아웃 설정
st.set_page_config(page_title="국가별 MBTI 데이터 분석기", layout="wide")

st.title("🌍 글로벌 MBTI 데이터 대시보드")
st.markdown("국가별로 16가지 MBTI 성격 유형의 분포를 비교하고, 특정 MBTI가 가장 많이 나타나는 국가를 탐색해보세요.")

# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    df = pd.read_csv("countriesMBTI_16types.csv")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일을 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 16가지 MBTI 유형 리스트 추출 (Country 열 제외)
mbti_types = [col for col in df.columns if col != "Country"]

# 💡 대시보드 구성을 위해 2개의 탭 생성
tab1, tab2 = st.tabs(["🗺️ 국가별 MBTI 분포 조회", "📊 MBTI별 상위 국가 TOP 10"])


# ------------------------------------------------------------------
# 탭 1: 국가별 MBTI 분포 조회 (기존 기능)
# ------------------------------------------------------------------
with tab1:
    st.header("국가별 MBTI 유형 순위")
    countries = sorted(df["Country"].unique())
    
    # 기본 선택값 설정 (South Korea가 있다면 선택, 없으면 첫 번째 국가)
    default_index = 0
    if "South Korea" in countries:
        default_index = countries.index("South Korea")
    elif "Korea, South" in countries:
        default_index = countries.index("Korea, South")
        
    selected_country = st.selectbox("조회할 국가를 선택하세요:", countries, index=default_index, key="tab1_country")
    
    # 데이터 추출 및 백분율 변환
    country_data = df[df["Country"] == selected_country].iloc[0]
    percentages = [country_data[mbti] * 100 for mbti in mbti_types]
    
    mbti_df = pd.DataFrame({
        "MBTI": mbti_types,
        "Percentage": percentages
    }).sort_values(by="Percentage", ascending=False).reset_index(drop=True)
    
    # 1등 빨간색, 나머지 파란색 그라데이션
    colors_tab1 = []
    for i in range(len(mbti_df)):
        if i == 0:
            colors_tab1.append("#FF4B4B")
        else:
            intensity = int(50 + (i / len(mbti_df)) * 160)
            colors_tab1.append(f"rgb({intensity}, {intensity + 40}, 255)")
            
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=mbti_df["MBTI"],
        y=mbti_df["Percentage"],
        text=mbti_df["Percentage"].round(2).astype(str) + "%",
        textposition='outside',
        marker=dict(color=colors_tab1, line=dict(color='rgba(0,0,0,0.1)', width=1)),
        hovertemplate="<b>%{x}</b><br>비율: %{y:.2f}%<extra></extra>"
    ))
    
    fig1.update_layout(
        title=dict(text=f"📊 <b>{selected_country}의 MBTI 유형별 비율 순위</b>", font=dict(size=18)),
        xaxis=dict(title="MBTI 유형"),
        yaxis=dict(title="비율 (%)", ticksuffix="%"),
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    fig1.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=True, zerolinecolor='rgba(0,0,0,0.1)')
    st.plotly_chart(fig1, use_container_width=True)


# ------------------------------------------------------------------
# 탭 2: MBTI별 상위 국가 TOP 10 (새로 추가된 기능 🚀)
# ------------------------------------------------------------------
with tab2:
    st.header("특정 MBTI 비율이 가장 높은 국가 TOP 10")
    
    # 사용자가 MBTI 16개 중 하나를 선택할 수 있는 셀렉트박스
    selected_mbti = st.selectbox("조회할 MBTI 유형을 선택하세요:", sorted(mbti_types), index=0, key="tab2_mbti")
    
    # 선택된 MBTI 기준으로 내림차순 정렬 후 상위 10개국 추출
    top10_df = df[['Country', selected_mbti]].copy()
    top10_df[selected_mbti] = top10_df[selected_mbti] * 100  # 백분율(%)로 변환
    top10_df = top10_df.sort_values(by=selected_mbti, ascending=False).head(10).reset_index(drop=True)
    
    # 색상 조건 반영: 1등은 빨간색, 2~10등은 점차 연해지는 파란색 그라데이션 적용
    colors_tab2 = []
    for i in range(len(top10_df)):
        if i == 0:
            colors_tab2.append("#FF4B4B")  # 1등 국가 빨간색
        else:
            # 순위가 낮아질수록(i가 증가할수록) RGB 값을 높여 연한 파란색 생성
            intensity = int(50 + (i / len(top10_df)) * 140)
            colors_tab2.append(f"rgb({intensity}, {intensity + 40}, 255)")
            
    # 플로틀리 인터랙티브 막대그래프 생성
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=top10_df["Country"],
        y=top10_df[selected_mbti],
        text=top10_df[selected_mbti].round(2).astype(str) + "%",
        textposition='outside',
        marker=dict(color=colors_tab2, line=dict(color='rgba(0,0,0,0.1)', width=1)),
        hovertemplate="<b>%{x}</b><br>비율: %{y:.2f}%<extra></extra>"
    ))
    
    fig2.update_layout(
        title=dict(text=f"👑 <b>전 세계 {selected_mbti} 비율 상위 10개국</b>", font=dict(size=18)),
        xaxis=dict(title="국가", tickangle=25),  # 국가명이 길 경우 겹치지 않도록 글자 살짝 회전
        yaxis=dict(title="비율 (%)", ticksuffix="%"),
        margin=dict(l=40, r=40, t=60, b=80),
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    fig2.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=True, zerolinecolor='rgba(0,0,0,0.1)')
    st.plotly_chart(fig2, use_container_width=True)
    
    # 하단에 깔끔한 데이터 요약 표 추가
    st.subheader(f"📋 {selected_mbti} 상위 10개국 상세 데이터")
    display_df = top10_df.copy()
    display_df.index = display_df.index + 1  # 인덱스를 1등부터 표시되도록 변경
    display_df.columns = ["국가명", "비율"]
    display_df["비율"] = display_df["비율"].round(2).astype(str) + "%"
    st.dataframe(display_df, use_container_width=True)
