# pip install fastapi uvicorn
from fastapi import FastAPI, Request, HTTPException
app = FastAPI()

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import uuid
import httpx

sessions = set()
async def create_book_session():
    session_id = str(uuid.uuid4())
    url = "http://localhost:8000/apps/book_agent/users/user1/sessions/" + session_id
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        response.raise_for_status()

        data = response.json()
        return data.get("id", session_id)

async def invoke_agent(session_id: str, user_message: str = "") -> str:
    url = "http://localhost:8000/run"
    payload = {
        "app_name": "book_agent",
        "user_id": "user1",
        "session_id": session_id,
        "new_message": { "role": "user", "parts": [{ "text": user_message }] },
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return data[0]["content"]["parts"][0]["text"]

@app.post("/session")
async def create_session():
    session_id = await create_book_session()
    sessions.add(session_id)
    return {"session_id": session_id}

@app.post("/greetings")
async def greetings(request: Request):
    data = await request.json()
    session_id = data.get("session_id")

    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    greet_msg = await invoke_agent(session_id)
    print(f"Greeting message: {greet_msg}")
    return {"text": greet_msg, "session_id": session_id}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    user_message = data.get("text", "")

    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    reply = await invoke_agent(session_id, user_message)
    print(f"reply: {reply}")
    return {"text": reply, "session_id": session_id}

# FastAPI 실행 명령: uvicorn server:app --host 0.0.0.0 --port 5000
