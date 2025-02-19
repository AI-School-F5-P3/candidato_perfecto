import streamlit as st

if 'page' not in st.session_state:
    st.session_state.page = 'ranking'
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'selected_cvs' not in st.session_state:
    st.session_state.selected_cvs = []

session_state = st.session_state