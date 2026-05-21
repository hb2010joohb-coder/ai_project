import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="국가별 MBTI 데이터 시각화", layout="wide")

st.title("🌍 국가별 MBTI 16가지 성격 유형 분석")
st.markdown("공공 또는 연구 데이터를 기반으로 한 국가별 MBTI 비율을 확인하고 비교해보세요.")

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

# 사이드바 - 국가 선택
st.sidebar.header("설정")
countries = sorted(df["Country"].unique())

# 기본 선택값 설정 (South Korea가 있다면 선택, 없으면 첫 번째 국가)
default_index = 0
if "South Korea" in countries:
    default_index = countries.index("South Korea")
elif "Korea, South" in countries:
    default_index = countries.index("Korea, South")

selected_country = st.sidebar.selectbox("🗺️ 국가를 선택하세요", countries, index=default_index)

# 선택된 국가의 데이터 추출
country_data = df[df["Country"] == selected_country].iloc[0]

# MBTI 유형과 비율을 데이터프레임으로 변환 (Country 열 제외)
mbti_types = [col for col in df.columns if col != "Country"]
percentages = [country_data[mbti] * 100 for mbti in mbti_types]  # 백분율(%)로 변환

mbti_df = pd.DataFrame({
    "MBTI": mbti_types,
    "Percentage": percentages
}).sort_values(by="Percentage", ascending=False).reset_index(drop=True)

# 1등 찾기 및 색상 배열 생성 (1등 빨간색, 나머지는 파란색 그라데이션)
colors = []
for i in range(len(mbti_df)):
    if i == 0:
        colors.append("#FF4B4B")  # 1등: 스트림릿 시그니처 레드
    else:
        # 2등부터 16등까지 파란색 그라데이션 계산 (순위가 낮아질수록 연한 파란색)
        intensity = int(50 + (i / len(mbti_df)) * 160)
        colors.append(f"rgb({intensity}, {intensity + 40}, 255)")

# Plotly 차트 생성
fig = go.Figure()

fig.add_trace(go.Bar(
    x=mbti_df["MBTI"],
    y=mbti_df["Percentage"],
    text=mbti_df["Percentage"].round(2).astype(str) + "%",
    textposition='outside',
    marker=dict(
        color=colors,
        line=dict(color='rgba(0,0,0,0.1)', width=1)
    ),
    hovertemplate="<b>%{x}</b><br>비율: %{y:.2f}%<extra></extra>"
))

# 레이아웃 정돈 (★오류 수정 반영 완료)
fig.update_layout(
    title=dict(
        text=f"📊 <b>{selected_country}의 MBTI 유형별 비율 순위</b>",  # HTML <b> 태그로 bold 적용
        font=dict(size=20)
    ),
    xaxis=dict(title="MBTI 유형", tickangle=0),
    yaxis=dict(title="비율 (%)", ticksuffix="%"),  # suffix -> ticksuffix 로 수정
    margin=dict(l=40, r=40, t=60, b=40),
    height=550,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

# 그리드선 추가 (Y축만)
fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=True, zerolinecolor='rgba(0,0,0,0.1)')

# 스트림릿에 차트 띄우기
st.plotly_chart(fig, use_container_width=True)

# 간단한 데이터 테이블 및 요약 정보 제공
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💡 주요 특징")
    top_1 = mbti_df.iloc[0]
    top_2 = mbti_df.iloc[1]
    st.markdown(f"**{selected_country}**에서 가장 많은 MBTI 유형은 **{top_1['MBTI']}**입니다. (전체의 **{top_1['Percentage']:.2f}%**)")
    st.markdown(f"두 번째로 많은 유형은 **{top_2['MBTI']}** (**{top_2['Percentage']:.2f}%**)입니다.")

with col2:
    st.subheader("📋 전체 데이터 표")
    formatted_df = mbti_df.copy()
    formatted_df["Percentage"] = formatted_df["Percentage"].round(2).astype(str) + "%"
    formatted_df.columns = ["MBTI 유형", "비율"]
    st.dataframe(formatted_df, use_container_width=True, height=200)
