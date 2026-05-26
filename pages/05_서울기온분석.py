import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# 한글 폰트 설정 (Linux 기반의 Streamlit Cloud 환경 고려)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

st.title("🌡️ 서울 기온 데이터 분석 앱")
st.markdown("1907년부터의 서울 기온 데이터를 바탕으로 특정 날짜의 연도별 기온 변화를 분석합니다.")

# 1. 데이터 로드 함수 (여러 인코딩 자동 감지 및 캐싱 적용)
@st.cache_data
def load_data():
    if not os.path.exists("seoul.csv"):
        st.error("⚠️ 'seoul.csv' 파일을 찾을 수 없습니다. 앱과 같은 디렉토리에 파일을 위치시켜주세요.")
        return None

    # 시도할 인코딩 목록
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
    df = None
    
    # 성공할 때까지 인코딩을 바꾸며 읽기 시도
    for encoding in encodings:
        try:
            df = pd.read_csv("seoul.csv", encoding=encoding)
            break  # 읽기 성공 시 반복문 탈출
        except UnicodeDecodeError:
            continue
            
    # 모든 인코딩이 실패했을 경우 예외 처리
    if df is None:
        st.error("⚠️ 파일의 인코딩을 인식할 수 없습니다. 파일을 UTF-8 또는 CP949 형식으로 다시 저장해 주세요.")
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

# 데이터 로드 실행
df = load_data()

if df is not None:
    # 2. 사용자 입력 받아오기 (사이드바 이용)
    st.sidebar.header("📅 날짜 선택")
    selected_month = st.sidebar.selectbox("월(Month)을 선택하세요", list(range(1, 13)), index=7) # 기본값 8월
    selected_day = st.sidebar.selectbox("일(Day)을 선택하세요", list(range(1, 32)), index=14)   # 기본값 15일
    
    # 3. 데이터 필터링 (선택한 월과 일에 해당하는 데이터 추출)
    filtered_df = df[(df['월'] == selected_month) & (df['일'] == selected_day)].sort_values('연도')
    
    if filtered_df.empty:
        st.warning(f"선택하신 {selected_month}월 {selected_day}일에 해당하는 데이터가 없습니다. 다른 날짜를 선택해주세요.")
    else:
        st.subheader(f"📊 {selected_month}월 {selected_day}일의 연도별 기온 변화")
        
        # 4. 꺾은선 그래프 그리기
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # 최고기온은 핫핑크(hotpink), 최저기온은 연한 파란색(lightblue)으로 지정
        ax.plot(filtered_df['연도'], filtered_df['최고기온(℃)'], color='hotpink', marker='o', markersize=3, label='Max Temp (최고기온)')
        ax.plot(filtered_df['연도'], filtered_df['최저기온(℃)'], color='lightblue', marker='o', markersize=3, label='Min Temp (최저기온)')
        
        # 그래프 제목, 가로축(연도), 세로축(온도) 설정
        ax.set_title("날짜별 기온분석", fontsize=14, pad=15)
        ax.set_xlabel("연도", fontsize=11)
        ax.set_ylabel("온도 (℃)", fontsize=11)
        
        # 범례 표시 및 그리드 설정
        ax.legend(loc='best')
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # 스트림릿 웹 화면에 그래프 출력
        st.pyplot(fig)
        
        # 5. 역대 극값 통계 요약 (시각적 효과)
        st.markdown("---")
        st.markdown(f"### 💡 {selected_month}월 {selected_day}일 역대 기록 요약")
        col1, col2 = st.columns(2)
        
        with col1:
            max_row = filtered_df.loc[filtered_df['최고기온(℃)'].idxmax()]
            st.metric(label="역대 최고 기온", value=f"{max_row['최고기온(℃)']} ℃", delta=f"{int(max_row['연도'])}년")
            
        with col2:
            min_row = filtered_df.loc[filtered_df['최저기온(℃)'].idxmin()]
            st.metric(label="역대 최저 기온", value=f"{min_row['최저기온(℃)']} ℃", delta=f"{int(min_row['연도'])}년")
