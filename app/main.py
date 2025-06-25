from fastapi import FastAPI, HTTPException
from app.schema import ReviewIn
from app.database import SessionLocal
from app.models import Review
from app.load_model import predict_category
import uuid

app = FastAPI()
db = SessionLocal()

# Temporary memory to simulate user sessions
user_sessions = {}


@app.get("/start")
def start_conversation():
    session_id = str(uuid.uuid4())
    user_sessions[session_id] = {}
    return {
        "session_id": session_id,
        "message": "Welcome! Please leave a review, complaint, or suggestion.",
        "input_enabled": True
    }


@app.post("/submit_review")
def submit_review(session_id: str, review: ReviewIn):
    if session_id not in user_sessions:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    predicted = predict_category(review.text)
    user_sessions[session_id] = {
        "text": review.text,
        "predicted": predicted
    }
    return {
        "entered_text": review.text,
        "predicted_category": predicted,
        "message": f'You wrote: "{review.text}"\nI think it belongs to the category: **{predicted}**. Do you confirm?',
        "confirm_buttons": ["yes", "no"],
        "input_enabled": False
    }


@app.post("/confirm")
def confirm_review(session_id: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    data = user_sessions[session_id]
    review = Review(text=data["text"], category=data["predicted"])
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "message": "✅ Thank you! Your review has been saved.",
        "input_enabled": True
    }


@app.post("/reject")
def reject_prediction(session_id: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    categories = [
        "Premium Features", "User Feedbacks & Recommendations",
        "General Topics", "Ads", "Crashes and Bugs",
        "Updates", "Customer Support"
    ]
    return {
        "message": "❌ No problem. Please select the correct category below:",
        "categories": categories,
        "input_enabled": False
    }


@app.post("/assign_manual")
def assign_manual(session_id: str, category: str):
    if session_id not in user_sessions:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    data = user_sessions[session_id]
    review = Review(text=data["text"], category=category)
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "message": f"✅ Your review has been saved with the selected category: {category}.",
        "input_enabled": True
    }
