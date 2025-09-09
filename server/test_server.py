# pip install fastapi uvicorn
from fastapi import FastAPI, Request, HTTPException
import uuid

app = FastAPI()
sessions = set()

@app.post("/session")           # localhost:5000/session
async def create_session():
    session_id = str(uuid.uuid4())
    sessions.add(session_id)
    return {"session_id": session_id}

@app.post("/greetings")         # localhost:5000/greetings
async def greetings(request: Request):
    data = await request.json()
    session_id = data.get("session_id")

    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    greet_msg = "무엇을 도와 드릴까요?"
    return {"text": greet_msg, "session_id": session_id}

@app.post("/chat")              # localhost:5000/chat
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    user_message = data.get("text", "")

    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    print(f"[{session_id}] User: {user_message}")
    reply = input(f"[{session_id}] Agent: ")

    return {"text": reply, "session_id": session_id}

# FastAPI 실행 명령: uvicorn test_server:app --host 0.0.0.0 --port 5000
