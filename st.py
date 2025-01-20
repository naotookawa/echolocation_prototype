import streamlit as st

# Streamlit UI
st.title("リアルタイム音声処理設定")
settings.decay = st.slider("Decay", 0.1, 10.0, 4.0, 0.1)
settings.position = st.slider("Position", 0.0, 10.0, 5.0, 0.1)

if st.button("リアルタイム処理を開始"):
    start_stream()
