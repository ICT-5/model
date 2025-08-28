from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from services import start_interview, answer_and_followup#, run_full_interview
from db_utils import end_session
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

#start
class StartRequest(BaseModel):
    user_id: int
    interview_type: str
    personality: str

class AnswerRequest(BaseModel):
    question_id: int
    answer: str
    interview_type: str
    personality: str
    keywords: List[str]

#class AutoRunRequest(BaseModel):
#    user_id: int
#    interview_type: str
#    personality: str
#    keywords: list[str]

class EndRequest(BaseModel):
    reason: str

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/api/simulation/session")
def start(req: StartRequest):
    session_id, questions, keywords = start_interview(req.user_id, req.interview_type)
    return {
        "session_id": session_id,
        "questions": questions,
        "keywords": keywords,
        "personality": req.personality
    }

@app.post("/api/simulation/{session_id}/answer")
def answer(session_id: int, req: AnswerRequest):
    follow_up, qid = answer_and_followup(session_id, req.question_id, req.answer, req.keywords, req.interview_type, req.personality)
    return {"follow_up": follow_up, "question_id": qid}

#@app.post("/session/autorun")
#def autorun(req: AutoRunRequest):
#    result = run_full_interview(req.user_id, req.interview_type, req.personality, req.keywords)
#    return result

@app.post("/api/simulation/{session_id}/end")
def end(session_id: int, req: EndRequest):
    end_session(session_id, req.reason)
    return {"status": "ended", "reason": req.reason}
