import streamlit as st

st.set_page_config(
    page_title="backtesting-engine",
    page_icon="📈",
)

readme_content = ""
with open('README.md', 'r') as file:
    readme_content = file.read()

st.markdown(readme_content)
