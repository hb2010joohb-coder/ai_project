import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import urllib.request

# 1. 스트림릿 클라우드 환경을 위한 한글 폰트 설정
@st.cache_data
def load_korean_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    font_path = "NanumGothic-Regular.ttf"
    try:
        urllib.request.urlretrieve(font_url, font_path)
        fe = fm.FontEntry(fname=font_path, name='NanumGothic')
        fm.font_manager.ttflist.insert(0, fe)
        plt.rcParams['font.family'] = 'NanumGothic'
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        st.warning(f"한글 폰트 로드 중 오류가 발생했습니다. 기본 폰트를 사용합니다. ({e})")

load_korean_font()

# 2. 데이터 불러오기 및 전처리
@st.cache_data
def load_data():
    df = pd.read_csv("population.csv", encoding="cp949")
    df.columns = [col.replace('ㅏ', '') for col in df.columns]
    df['행정구역_표시'] = df['행정구역'].apply(lambda x: x.split('(')[0].strip())
    
    age_columns = [col for col in df.columns if col not in ['행정구역', '행정구역_표시']]
    for col in age_columns:
        df[col] = df[col].astype(str).str.replace(',', '').astype(int)
        
    return df, age_columns

try:
    df, age_cols = load_data()
except Exception as e:
    st.error(f"데이터 파일을 읽어오는 데 실패했습니다. 에러: {e}")
    st.stop()

# 3. 스트림릿 UI 구성
st.title("📌 서울시 자치구별 인구 구조 분석")
st.markdown("공공데이터를 바탕으로 구별 연령대 인구수를 꺾은선 그래프로 시각화합니다.")

selected_region = st.selectbox(
    "조회할 행정구를 선택하세요:",
    options=df['행정구역_표시'].tolist(),
    index=0
)

selected_data = df[df['행정구역_표시'] == selected_region].iloc[0]
population_values = [selected_data[col] for col in age_cols]

# 4. 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor('#F0E6FF') 
ax.set_facecolor('#F8F3FF')

ax.plot(age_cols, population_values, color='red', marker='o', linewidth=2, markersize=6)

ax.set_title("서울시의 인구통계", fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel("연령대", fontsize=12, labelpad=10)
ax.set_ylabel("인구수 (명)", fontsize=12, labelpad=10)

ax.grid(True, linestyle='--', alpha=0.5, color='#D1C4E9')
ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)

# 5. 연령대별 인구 최다 자치구 요약 정보
st.markdown("---")
st.header("🏆 연령대별 인구 최다 자치구 TOP 3")
st.markdown("전체 서울시 데이터를 제외한 25개 자치구 중에서 인구가 가장 많은 구를 분석한 결과입니다.")

gu_df = df[df['행정구역_표시'] != '서울특별시'].copy()
tabs = st.tabs(age_cols)

for i, age_col in enumerate(age_cols):
    with tabs[i]:
        st.subheader(f"🥇 {age_col} 인구가 가장 많은 자치구")
        top3 = gu_df.sort_values(by=age_col, ascending=False).head(3)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="1위 🥇", 
                value=top3.iloc[0]['행정구역_표시'].replace("서울특별시 ", ""), 
                delta=f"{top3.iloc[0][age_col]:,}명"
            )
        with col2:
            st.metric(
                label="2위 🥈", 
                value=top3.iloc[1]['행정구역_표시'].replace("서울특별시 ", ""), 
                delta=f"{top3.iloc[1][age_col]:,}명"
            )
        with col3:
            st.metric(
                label="3위 🥉", 
                value=top3.iloc[2]['행정구역_표시'].replace("서울특별시 ", ""), 
                delta=f"{top3.iloc[2][age_col]:,}명"
            )

st.markdown("---")
with st.expander("📊 상세 데이터 보기"):
    detail_df = pd.DataFrame({
        '연령대': age_cols,
        '인구수(명)': [f"{val:,}" for val in population_values]
    })
    st.dataframe(detail_df.set_index('연령대'), use_container_width=True)
