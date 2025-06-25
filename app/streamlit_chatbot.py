import streamlit as st
import requests

API_URL = "http://localhost:8000"

# --- Custom CSS for modern look ---
st.markdown("""
    <style>
    .main {
        background-color: #f7f8fa;
    }
    .stTextInput>div>div>input {
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        background: #fff;
        padding: 10px;
        color: #222 !important; /* <-- Add this line for visible text */
        font-size: 1.1em;
    }
    .stButton>button {
        border-radius: 12px;
        background: linear-gradient(90deg, #6dd5ed 0%, #2193b0 100%);
        color: white;
        border: none;
        padding: 0.5em 2em;
        margin: 0.2em 0;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(33,147,176,0.08);
        transition: background 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2193b0 0%, #6dd5ed 100%);
    }
    .message-bubble {
        border-radius: 16px;
        padding: 1em;
        margin-bottom: 0.5em;
        box-shadow: 0 2px 8px rgba(33,147,176,0.06);
        background: #fff;
        display: inline-block;
        max-width: 80%;
    }
    .bot {
        background: #e3f6fc;
        color: #1a3c4c;
    }
    .user {
        background: #d1e7dd;
        color: #1a3c4c;
        margin-left: auto;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session management ---
if "session_id" not in st.session_state:
    response = requests.get(f"{API_URL}/start")
    st.session_state.session_id = response.json()["session_id"]
    st.session_state.messages = []
    st.session_state.waiting_confirmation = False
    st.session_state.predicted_category = None
    st.session_state.input_disabled = False

# --- App title ---
st.markdown("<h1 style='color:#2193b0; font-weight:700;'>💬 AI Feedback Classifier Chatbot</h1>",
            unsafe_allow_html=True)

# --- Message display ---
for msg in st.session_state.messages:
    role = "🤖 Bot" if msg["from"] == "bot" else "🙋 You"
    bubble_class = "bot" if msg["from"] == "bot" else "user"
    st.markdown(
        f"<div class='message-bubble {bubble_class}'><b>{role}:</b> {msg['text']}</div>",
        unsafe_allow_html=True
    )

# --- Input field ---
if not st.session_state.input_disabled:
    user_input = st.text_input(
        "Write your review or complaint here:", key="input_text")
    if st.button("Send"):
        if user_input.strip() != "":
            res = requests.post(f"{API_URL}/submit_review?session_id={st.session_state.session_id}", json={
                "text": user_input
            })
            if res.status_code == 200:
                result = res.json()
                st.session_state.messages.append(
                    {"from": "user", "text": user_input})
                st.session_state.messages.append(
                    {"from": "bot", "text": result.get("message", "⚠️ Unexpected API response.")})
                st.session_state.predicted_category = result.get(
                    "predicted_category")
                st.session_state.waiting_confirmation = True
                st.session_state.input_disabled = True
                st.rerun()
            else:
                st.error("❌ Something went wrong with the API.")
                st.write(res.json())

# --- Confirmation buttons ---
if st.session_state.waiting_confirmation:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, correct"):
            res = requests.post(
                f"{API_URL}/confirm?session_id={st.session_state.session_id}")
            if res.status_code == 200:
                st.session_state.messages.append(
                    {"from": "bot", "text": res.json().get("message", "⚠️ Unexpected API response.")})
                st.success("Your review has been saved! 🎉")
                st.balloons()
            else:
                st.session_state.messages.append(
                    {"from": "bot", "text": "⚠️ API error: " + res.text})
            st.session_state.waiting_confirmation = False
            st.session_state.input_disabled = False
            st.rerun()
    with col2:
        if st.button("❌ No, choose another"):
            res = requests.post(
                f"{API_URL}/reject?session_id={st.session_state.session_id}")
            st.session_state.messages.append(
                {"from": "bot", "text": res.json().get("message", "⚠️ Unexpected API response.")})
            st.session_state.input_disabled = True
            st.session_state.waiting_confirmation = False
            st.session_state.choose_category = True
            st.rerun()

# --- Category choices ---
if st.session_state.get("choose_category", False):
    st.markdown("### Choose the correct category:")
    categories = [
        "Premium Features", "User Feedbacks & Recommendations",
        "General Topics", "Ads", "Crashes and Bugs",
        "Updates", "Customer Support"
    ]
    for cat in categories:
        if st.button(cat):
            res = requests.post(
                f"{API_URL}/assign_manual?session_id={st.session_state.session_id}&category={cat}")
            if res.status_code == 200:
                st.session_state.messages.append(
                    {"from": "bot", "text": res.json().get("message", "⚠️ Unexpected API response.")})
                st.success("Your review has been saved! 🎉")
                st.balloons()
            else:
                st.session_state.messages.append(
                    {"from": "bot", "text": "⚠️ API error: " + res.text})
            st.session_state.input_disabled = False
            st.session_state.choose_category = False
            st.rerun()
