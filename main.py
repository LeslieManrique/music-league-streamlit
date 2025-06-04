# main.py
import streamlit as st

st.markdown("""
    <div style="background-color:#9e01c4;padding:1rem 1.5rem;margin-bottom:1.5rem;border-radius:8px">
        <h1 style="color:white;text-align:center;font-size:3rem;">🎧Music League Dashboard🎧</h1>
        <p style="color:white;text-align:center;font-size:1rem;margin-top:0.5rem;">Choose a season below</p>
    </div>
""", unsafe_allow_html=True)
# Add centered season buttons
st.markdown("""
<div style="text-align:center;">
    <h2 style="color:#9e01c4;">Available Seasons</h2>
</div>
""", unsafe_allow_html=True)

# Minimalist styled buttons without hyperlink styling
st.markdown("""
    <style>
    .season-button {
        display: inline-block;
        background-color: transparent;
        color: #9e01c4;
        border: 2px solid #9e01c4;
        text-align: center;
        padding: 1rem 2rem;
        font-size: 1.25rem;
        font-weight: 500;
        border-radius: 12px;
        margin: 1rem;
        text-decoration: none !important;
        transition: background-color 0.3s, color 0.3s;
    }
    .season-button:hover {
        background-color: #9e01c4;
        color: white;
    }
    a.season-button:link, a.season-button:visited, a.season-button:hover, a.season-button:active {
        text-decoration: none !important;
        color: inherit;
    }
    </style>
    <div style="text-align:center;">
        <a href="/music_league_s1_dashboard" class="season-button">❤️ Season 1: Overwatch 3 Waiting Room</a>
        <a href="/music_league_s2_dashboard" class="season-button">❤️ Season 2: Marvel Rivals Waiting Room</a>
    </div>
""", unsafe_allow_html=True)

# Fun extra space
st.markdown("""
<div style="margin-top: 2rem;"></div>
""", unsafe_allow_html=True)

# Footer styling
st.markdown("""
    <style>
        footer {
            visibility: hidden;
        }
        .css-cio0dv.egzxvld1 {
            visibility: visible;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            color: #9e01c4;
            text-align: center;
            padding: 0.5rem;
            font-size: 0.85rem;
        }
    </style>
    <div class="css-cio0dv egzxvld1">Made with ❤️ by Leslie & ChatGPT</div>
""", unsafe_allow_html=True)
