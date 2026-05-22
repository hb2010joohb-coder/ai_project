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
    # 인코딩 에러 방지를 위해 cp949 적용
    df = pd.read_csv("population.csv", encoding="cp949")
    
    # 마지막 컬럼명 오타('ㅏ100세 이상') 수정 및 통일
    df.columns = [col.replace('ㅏ', '') for col in df.columns]
    
    # 행정구역 이름 깔끔하게 정리 (예: "서울특별시 종로구 (1111000000)" -> "서울특별시 종로구")
    df['행정구역_표시'] = df['행정구역'].apply(lambda x: x.split('(')[0].strip())
    
    # 숫자 데이터의 콤마(,) 제거 후 정수형 변환
    age_columns = [col for col in df.columns if col not in ['행정구역', '행정구역_표시']]
    for col in age_columns:
        df[col] = df[col].astype(str).str.replace(',', '').astype(int)
        
    return df, age_columns

try:
    df, age_cols = load_data()
except Exception as e:
    st.error(f"데이터 파일을 읽어오는 데 실패했습니다. 'population.csv' 파일의 인코딩을 확인해주세요. 에러: {e}")
    st.stop()

# 3. 스트림릿 UI 구성
st.title("📌 서울시 자치구별 인구 구조 분석")
st.markdown("공공데이터를 바탕으로 구별 연령대 인구수를 꺾은선 그래프로 시각화합니다.")

# 행정구 선택 셀렉트박스 (기본값은 '서울특별시' 전체)
selected_region = st.selectbox(
    "조회할 행정구를 선택하세요:",
    options=df['행정구역_표시'].tolist(),
    index=0
)

# 선택한 행정구의 데이터 추출
selected_data = df[df['행정구역_표시'] == selected_region].iloc[0]
population_values = [selected_data[col] for col in age_cols]

# 4. 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 5))

# 그래프 바탕색 설정 (연한 보라색 계열)
fig.patch.set_facecolor('#F0E6FF') 
ax.set_facecolor('#F8F3FF')

# 꺾은선 그래프 그리기 (빨간색)
ax.plot(age_cols, population_values, color='red', marker='o', linewidth=2, markersize=6)

# 그래프 제목 및 레이블 설정
ax.set_title("서울시의 인구통계", fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel("연령대", fontsize=12, labelpad=10)
ax.set_ylabel("인구수 (명)", fontsize=12, labelpad=10)

# 스타일 보완
ax.grid(True, linestyle='--', alpha=0.5, color='#D1C4E9')
ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
plt.xticks(rotation=45)
plt.tight_layout()

# 스트림릿에 그래프 출력
st.pyplot(fig)


# ==========================================
# [추가 기능] 5. 연령대별 인구가 많은 자치구 요약 정보
# ==========================================
st.markdown("---")
st.header("🏆 연령대별 인구 최다 자치구 TOP 3")
st.markdown("전체 서울시 데이터를 제외한 25개 자치구 중에서 인구가 가장 많은 구를 분석한 결과입니다.")

# '서울특별시' 전체 데이터를 제외하고 자치구만 필터링
# 보통 자치구는 행정구역 표시 이름이 '서울특별시'보다 깁니다 (예: 서울특별시 종로구)
gu_df = df[df['행정구역_표시'] != '서울특별시'].copy()

# 탭을 활용해 모든 연령대를 깔끔하게 나누어 시각화
tabs = st.tabs(age_cols)

for i, age_col in enumerate(age_cols):
    with tabs[i]:
        st.subheader(f"🥇 {age_col} 인구가 가장 많은 자치구")
        
        # 해당 연령대 기준 내림차순 정렬 후 상위 3개 추출
        top3 = gu_df.sort_values(by=age_col, ascending=False).head(3)
        
        # 가독성 좋은 카드 세 개 배치
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="1위 🥇", 
                value=
