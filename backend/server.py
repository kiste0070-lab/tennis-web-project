from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading

# bot.py에서 가져올 함수들
from bot import run_tennis_bot, stop_tennis_bot

app = FastAPI(title="테니스 자동 예약 봇 API")

# Vercel 웹사이트에서 이 서버로 접속할 수 있도록 CORS 통신 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 나중에 Vercel 도메인으로 제한 가능
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel에서 받아올 데이터 형식 지정 (입력 칸의 숫자)
class StartRequest(BaseModel):
    interval_minutes: int

# 예시용 전역 상태 변수 (실제 봇 연결 시 삭제)
BOT_STATUS = {"running": False, "interval": 0}

@app.get("/")
def read_root():
    return {"msg": "✅ 백엔드 봇 서버가 정상적으로 동작 중입니다!"}

@app.post("/start")
async def start_bot(req: StartRequest):
    if BOT_STATUS["running"]:
        return {"status": "error", "msg": "봇이 이미 데몬으로 돌고 있습니다!"}
    
    BOT_STATUS["running"] = True
    BOT_STATUS["interval"] = req.interval_minutes
    
    # 백그라운드로 봇 실행
    threading.Thread(target=run_tennis_bot, args=(req.interval_minutes,), daemon=True).start()
    
    print(f"🚀 웹에서 시작 요청 받음! 주기: {req.interval_minutes}분")
    return {"status": "success", "msg": f"테니스 예약 봇이 {req.interval_minutes}분 주기로 가동을 시작했습니다!"}

@app.post("/stop")
def stop_bot():
    if not BOT_STATUS["running"]:
        return {"status": "error", "msg": "실행 중인 봇이 없습니다."}
    
    BOT_STATUS["running"] = False
    BOT_STATUS["interval"] = 0
    stop_tennis_bot()
    print("🛑 웹에서 정지 요청 받음!")
    return {"status": "success", "msg": "테니스 예약 봇이 정지되었습니다."}

@app.get("/status")
def bot_status():
    return BOT_STATUS
