import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import db_utils
from database import init_db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: str
    password: str

class Entry(BaseModel):
    user_id: int
    text: str
    incognito: bool = False


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/register")

def register(user:User):
    success = db_utils.register_user(user.username, user.password)
    if success:
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")
@app.post("/login")

def login(user:User):
    user_id = db_utils.login_user(user.username, user.password)
    if user_id:
        return {"user_id": user_id}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")
@app.post("/analyze")

def analyze(entry: Entry):
    analysis_result = db_utils.analyze_entry(entry.user_id, entry.text, entry.incognito)
    if analysis_result:
        return {"analysis": analysis_result}
    else:
        raise HTTPException(status_code=500, detail="Analysis failed")
@app.get("/calendar")

def calendar(user_id: int, year: int, month: int):
    try:
        return db_utils.get_calendar(user_id, year, month)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID or date")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve calendar")
@app.get("/history")

def history(user_id: int, limit: int=20, offset:int =0, date: str = None):
    try:
        items = db_utils.get_user_analysis_history(user_id, limit, offset, date)
        return {"items": items}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID or date")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve history")
@app.delete("/history/{entry_id}")

def delete_entry(entry_id:int, user_id:int):
    success=db_utils.delete_entry(user_id, entry_id)
    if success:
        return {"message": "Entry deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete entry")
@app.get("/stats")

def get_stats(user_id: int):
    try:
        return db_utils.get_user_stats(user_id)
    except Exception as e:
        print(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")
@app.get("/fluctuation")

def get_fluctuation(user_id: int):
    try:
        fluctuation = db_utils.get_emotion_fluctuation(user_id)
        return {"fluctuation": fluctuation}
    except Exception as e:
        print(f"Error fetching fluctuation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fluctuation")
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
