import streamlit as st
st.title('나의 첫 웹서비스 만들기!')
a=st.text_input('이름을 입력하세요')
b=st.selectbox('좋아하는 음식을 선택하세요!',['볶음밥','간장게장','피자'])
if st.button('인사말 생성'):
  st.write(a+'님, 안녕하세요!')
           
