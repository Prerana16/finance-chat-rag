from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import ask_question

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finance-chat-rag.vercel.app/"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],   # or restrict to ["POST"]
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str

@app.post("/chat")
async def chat(q: Question):
    result = ask_question(q.question)
    return result