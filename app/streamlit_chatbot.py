import streamlit as st
import requests

API_URL = "http://localhost:8000"

# --- Session management ---
if "session_id" not in st.session_state:
    response = requests.get(f"{API_URL}/start")
    st.session_state.session_id = response.json()["session_id"]
    st.session_state.messages = []
    st.session_state.waiting_confirmation = False
    st.session_state.predicted_category = None
    st.session_state.input_disabled = False

# --- App title ---
st.title("💬 AI Feedback Classifier Chatbot")

# --- Message display ---
for msg in st.session_state.messages:
    role = "🤖 Bot" if msg["from"] == "bot" else "🙋 You"
    st.markdown(f"**{role}**: {msg['text']}")

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
            st.session_state.messages.append(
                {"from": "bot", "text": res.json().get("message", "⚠️ Unexpected API response.")})
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
            st.session_state.messages.append(
                {"from": "bot", "text": res.json().get("message", "⚠️ Unexpected API response.")})
            st.session_state.input_disabled = False
            st.session_state.choose_category = False
            st.rerun()
