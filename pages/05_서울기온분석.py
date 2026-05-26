import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Streamlit Cloud 환경용)
# 리눅스 서버 기반인 Streamlit Cloud에서는 나눔 폰트 등이 없을 수 있으므로 기본 폰트를 사용하거나 
# 한글이 깨질 경우 영어 레이블을 병행 표기하도록 설정합니다.
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

st.title("🌡️ 서울 기온 데이터 분석 앱")
st.markdown("1907년부터의 서울 기온 데이터를 바탕으로 특정 날짜의 연도별 기온 변화를 분석합니다.")

# 1. 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    # 파일명이 다를 경우를 대비해 업로드 기능을 제공하거나, 같은 경로의 seoul.csv를 읽습니다.
    try:
        df = pd.read_csv("seoul.csv")
    except FileNotFoundError:
        st.error("⚠️ 'seoul.csv' 파일을 찾을 수 없습니다. 앱과 같은 디렉토리에 파일을 위치시켜주세요.")
        return None
    
    # 날짜 컬럼의 앞뒤 공백 및 탭 문자(\t) 제거 후 datetime 변환
    df['날짜'] = df['날짜'].astype(str).str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    
    # 분석에 필요한 연, 월, 일 컬럼 추가
    df['연도'] = df['날짜'].dt.year
    df['월'] = df['날짜'].dt.month
    df['일'] = df['날짜'].dt.day
    
    # 기온 데이터 숫자형 변환 및 결측치 제거
    df['최고기온(℃)'] = pd.to_numeric(df['최고기온(℃)'], errors='coerce')
    df['최저기온(℃)'] = pd.to_numeric(df['최저기온(℃)'], errors='coerce')
    df = df.dropna(subset=['연도', '월', '일', '최고기온(℃)', '최저기온(℃)'])
    
    return df

df = load_data()

if df is not None:
    # 2. 사용자 입력 받아오기 (사이드바 이용)
    st.sidebar.header("📅 날짜 선택")
    selected_month = st.sidebar.selectbox("월(Month)을 선택하세요", list(range(1, 13)), index=7) # 기본값 8월
    
    # 선택한 월에 따른 일수 제한 (간단하게 1~31일 제공 후 예외처리)
    selected_day = st.sidebar.selectbox("일(Day)을 선택하세요", list(range(1, 32)), index=14) # 기본값 15일
    
    # 3. 데이터 필터링
    filtered_df = df[(df['월'] == selected_month) & (df['일'] == selected_day)].sort_values('연도')
    
    if filtered_df.empty:
        st.warning(f"선택하신 {selected_month}월 {selected_day}일에 해당하는 데이터가 없습니다. 다시 선택해주세요.")
    else:
        st.subheader(f"📊 {selected_month}월 {selected_day}일의 연도별 기온 변화")
        
        # 4. 꺾은선 그래프 그리기
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # 최고기온: 핫핑크(hotpink), 최저기온: 연한 파란색(lightblue)
        ax.plot(filtered_df['연도'], filtered_df['최고기온(℃)'], color='hotpink', marker='o', markersize=3, label='Max Temp (최고기온)')
        ax.plot(filtered_df['연도'], filtered_df['최저기온(℃)'], color='lightblue', marker='o', markersize=3, label='Min Temp (최저기온)')
        
        # 타이틀 및 축 레이블 설정
        ax.set_title("날짜별 기온분석 (Temperature Analysis by Date)", fontsize=14, pad=15)
        ax.set_xlabel("연도 (Year)", fontsize=11)
        ax.set_ylabel("온도 (Temperature, ℃)", fontsize=11)
        
        # 범례 표시
        ax.legend(loc='best')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # 스트림릿에 그래프 출력
        st.pyplot(fig)
        
        # 5. 간단한 데이터 통계 보여주기
        st.markdown("---")
        st.markdown(f"### 💡 {selected_month}월 {selected_day}일 역대 기록 요약")
        col1, col2 = st.columns(2)
        
        with col1:
            max_row = filtered_df.loc[filtered_df['최고기온(℃)'].idxmax()]
            st.metric(label="역대 최고 기온", value=f"{max_row['최고기온(℃)']} ℃", delta=f"{int(max_row['연도'])}년")
            
        with col2:
            min_row = filtered_df.loc[filtered_df['최저기온(℃)'].idxmin()]
            st.metric(label="역대 최저 기온", value=f"{min_row['최저기온(℃)']} ℃", delta=f"{int(min_row['연도'])}년")
