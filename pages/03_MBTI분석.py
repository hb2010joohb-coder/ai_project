import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 레이아웃 및 제목 설정
st.set_page_config(page_title="국가별 MBTI 데이터 시각화", layout="wide")

st.title("🌍 국가별 MBTI 16가지 성격 유형 분석")
st.markdown("공공 또는 연구 데이터를 기반으로 한 국가별 MBTI 비율을 확인하고 비교해보세요.")

# 2. 데이터 로드 함수 (캐싱 적용으로 속도 최적화)
@st.cache_data
def load_data():
    # 업로드하신 파일과 동일한 경로의 csv 파일 읽기
    df = pd.read_csv("countriesMBTI_16types.csv")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일('countriesMBTI_16types.csv')을 찾을 수 없거나 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 사이드바 - 국가 선택 필터 추가
st.sidebar.header("설정")
countries = sorted(df["Country"].unique())

# 기본 선택값 설정 (South Korea가 있다면 우선 선택, 없으면 첫 번째 국가)
default_index = 0
if "South Korea" in countries:
    default_index = countries.index("South Korea")
elif "Korea, South" in countries:
    default_index = countries.index("Korea, South")

selected_country = st.sidebar.selectbox("🗺️ 국가를 선택하세요", countries, index=default_index)

# 4. 선택된 국가의 MBTI 데이터 처리 (비율이 높은 순으로 정렬)
country_data = df[df["Country"] == selected_country].iloc[0]
mbti_types = [col for col in df.columns if col != "Country"]
percentages = [country_data[mbti] * 100 for mbti in mbti_types]  # 백분율(%) 변환

mbti_df = pd.DataFrame({
    "MBTI": mbti_types,
    "Percentage": percentages
}).sort_values(by="Percentage", ascending=False).reset_index(drop=True)

# 5. 요구사항 반영: 1등은 빨간색, 나머지는 파란색 그라데이션 색상 배열 생성
colors = []
for i in range(len(mbti_df)):
    if i == 0:
        colors.append("#FF4B4B")  # 1등: 강렬한 스트림릿 레드 계열
    else:
        # 2등부터 16등까지 순위가 내려갈수록(i가 커질수록) 연한 파란색이 되도록 RGB 값 계산
        intensity = int(50 + (i / len(mbti_df)) * 160)  # 50(진함)에서 210(연함) 사이로 조정
        colors.append(f"rgb({intensity}, {intensity + 40}, 255)")

# 6. 플로틀리(Plotly) 인터랙티브 막대그래프 그리기
fig = go.Figure()

fig.add_trace(go.Bar(
    x=mbti_df["MBTI"],
    y=mbti_df["Percentage"],
    text=mbti_df["Percentage"].round(2).astype(str) + "%", # 막대 위에 수치 표시
    textposition='outside',
    marker=dict(
        color=colors,
        line=dict(color='rgba(0,0,0,0.1)', width=1)
    ),
    hovertemplate="<b>%{x}</b><br>비율: %{y:.2f}%<extra></extra>"
))

# 그래프 레이아웃 스타일 정돈
fig.update_layout(
    title=dict(
        text=f"📊 {selected_country}의 MBTI 유형별 비율 순위",
        font=dict(size=20, bold=True)
    ),
    xaxis=dict(title="MBTI 유형"),
    yaxis=dict(title="비율 (%)", suffix="%"),
    margin=dict(l=40, r=40, t=60, b=40),
    height=550,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=True, zerolinecolor='rgba(0,0,0,0.1)')

# 스트림릿 화면에 차트 띄우기
st.plotly_chart(fig, use_container_width=True)

# 7. 하단에 추가 요약 정보 및 데이터 테이블 레이아웃 구성
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
