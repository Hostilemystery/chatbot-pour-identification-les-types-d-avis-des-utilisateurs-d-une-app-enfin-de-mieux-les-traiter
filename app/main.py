from fastapi import FastAPI, HTTPException
from app.schema import ReviewIn
from app.database import SessionLocal
from app.models import Review
from app.load_model import predict_category, predict_admin_intent
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


@app.post("/admin_query")
def admin_query(query: dict):
    db = SessionLocal()
    text = query.get("query", "")
    intent, params = predict_admin_intent(text)
    if intent in ["get_latest_reviews"]:
        n = params.get("n", 5)
        reviews = db.query(Review).order_by(Review.id.desc()).limit(n).all()
        db.close()
        return {"reviews": [{"id": r.id, "text": r.text, "category": r.category} for r in reviews]}
    elif intent in ["get_reviews_by_category"]:
        cat = params.get("category")
        if not cat:
            db.close()
            return {"error": "No category specified."}
        reviews = db.query(Review).filter(Review.category == cat).all()
        db.close()
        return {"reviews": [{"id": r.id, "text": r.text, "category": r.category} for r in reviews]}
    elif intent in ["count_total_reviews", "count"]:
        total = db.query(Review).count()
        db.close()
        return {"count": total}
    elif intent in ["count_reviews_by_category", "count_by_category"]:
        cat = params.get("category")
        if not cat:
            db.close()
            return {"error": "No category specified."}
        total = db.query(Review).filter(Review.category == cat).count()
        db.close()
        return {"count": total}
    elif intent == "get_review_by_id":
        review_id = params.get("id")
        if not review_id:
            db.close()
            return {"error": "No review ID specified."}
        review = db.query(Review).filter(Review.id == review_id).first()
        db.close()
        if review:
            return {"review": {"id": review.id, "text": review.text, "category": review.category}}
        else:
            return {"error": "Review not found."}
    elif intent == "search_by_keyword":
        keyword = params.get("keyword")
        if not keyword:
            db.close()
            return {"error": "No keyword specified."}
        reviews = db.query(Review).filter(
            Review.text.ilike(f"%{keyword}%")).all()
        db.close()
        return {"reviews": [{"id": r.id, "text": r.text, "category": r.category} for r in reviews]}
    else:
        db.close()
        return {"message": f"Intent '{intent}' not recognized."}
