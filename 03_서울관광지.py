import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Seoul Top 10 Tourist Spots",
    page_icon="🗺️",
    layout="wide"
)

# 제목 및 설명
st.title("🇰🇷 외국인이 사랑하는 서울 주요 관광지 Top 10")
st.markdown("""
Streamlit과 Folium을 활용하여 외국인 관광객들에게 가장 인기 있는 서울의 명소 10곳을 지도에 표시했습니다. 
마커를 클릭하면 상세 정보를 확인할 수 있습니다.
""")

# 데이터 정의
tourist_spots = [
    {"name": "경복궁 (Gyeongbokgung Palace)", "lat": 37.5796, "lon": 126.9770, "desc": "한국의 대표적인 조선시대 법궁, 한복 체험의 성지", "cat": "역사/문화"},
    {"name": "N서울타워 (N Seoul Tower)", "lat": 37.5512, "lon": 126.9882, "desc": "남산 꼭대기에서 서울 시내를 한눈에 내려다보는 전망대", "cat": "랜드마크"},
    {"name": "명동 쇼핑거리 (Myeongdong)", "lat": 37.5634, "lon": 126.9846, "desc": "K-뷰티, 길거리 음식, 쇼핑의 중심지", "cat": "쇼핑/음식"},
    {"name": "북촌한옥마을 (Bukchon Hanok Village)", "lat": 37.5829, "lon": 126.9835, "desc": "실제 주민들이 거주하는 전통 한옥 양식의 보존 주거지", "cat": "역사/문화"},
    {"name": "인사동 (Insa-dong)", "lat": 37.5744, "lon": 126.9875, "desc": "전통 공예품, 갤러리, 전통 찻집이 모여있는 문화의 거리", "cat": "역사/문화"},
    {"name": "동대문디자인플라자 (DDP)", "lat": 37.5668, "lon": 127.0096, "desc": "자하 하디드가 설계한 세계 최대 규모의 3차원 비정형 건축물", "cat": "랜드마크"},
    {"name": "홍대 거리 (Hongdae Street)", "lat": 37.5555, "lon": 126.9231, "desc": "젊은이들의 예술과 버스킹, 클럽 문화가 살아있는 곳", "cat": "젊음/문화"},
    {"name": "롯데월드타워 & 몰 (Lotte World Tower)", "lat": 37.5126, "lon": 127.1025, "desc": "세계에서 5번째로 높은 빌딩과 대형 쇼핑몰", "cat": "랜드마크"},
    {"name": "이태원 (Itaewon)", "lat": 37.5345, "lon": 126.9942, "desc": "다양한 문화와 이국적인 음식점들이 가득한 다국적 공간", "cat": "젊음/문화"},
    {"name": "광장시장 (Gwangjang Market)", "lat": 37.5701, "lon": 127.0010, "desc": "빈대떡, 육회, 마약김밥 등 한국 시장 음식을 체험하는 곳", "cat": "쇼핑/음식"}
]

color_dict = {
    "역사/문화": "red",
    "랜드마크": "blue",
    "쇼핑/음식": "green",
    "젊음/문화": "purple"
}

# 레이아웃 분할
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 서울 관광 지도")
    m = folium.Map(location=[37.555, 126.985], zoom_start=12)
    
    for spot in tourist_spots:
        popup_text = f"<b>{spot['name']}</b><br><br>{spot['desc']}"
        popup = folium.Popup(popup_text, max_width=300)
        
        folium.Marker(
            location=[spot["lat"], spot["lon"]],
            popup=popup,
            tooltip=spot["name"],
            icon=folium.Icon(color=color_dict.get(spot["cat"], "blue"), icon="info-sign")
        ).add_to(m)
    
    # 지도 렌더링
    st_folium(m, width="100%", height=600, returned_objects=[])

with col2:
    st.subheader("📌 명소 리스트 및 정보")
    st.markdown("**🎨 카테고리 안내**")
    for cat, color in color_dict.items():
        st.markdown(f"- <span style='color:{color}; font-weight:bold;'>■</span> {cat}", unsafe_allow_html=True)
    
    st.write("---")
    
    for idx, spot in enumerate(tourist_spots, 1):
        with st.expander(f"{idx}. {spot['name']}"):
            st.markdown(f"**카테고리:** {spot['cat']}")
            st.write(spot['desc'])
