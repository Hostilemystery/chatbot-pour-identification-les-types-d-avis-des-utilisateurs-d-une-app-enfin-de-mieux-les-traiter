from pydantic import BaseModel


class ReviewIn(BaseModel):
    text: str


class ReviewOut(BaseModel):
    text: str
    predicted_category: str
