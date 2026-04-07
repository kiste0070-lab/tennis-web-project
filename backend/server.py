from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import threading
import uuid

# bot.py에서 가져올 함수들
from bot import run_tennis_bot, stop_tennis_bot

app = FastAPI(title="테니스 자동 예약 봇 API")

# Vercel 웹사이트에서 이 서버로 접속할 수 있도록 CORS 통신 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 나중에 Vercel 도메인으로 제한 가능
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Vercel에서 받아올 데이터 형식 지정 (입력 칸의 숫자)
class StartRequest(BaseModel):
    interval_minutes: int


# 예시용 전역 상태 변수 (실제 봇 연결 시 삭제)
BOT_STATUS = {"running": False, "interval": 0}

# 로그 저장소 (메모리 내)
LOGS = []
LOG_LOCK = threading.Lock()


def add_log(level: str, message: str):
    """로그를 저장하는 함수"""
    with LOG_LOCK:
        LOGS.append(
            {
                "id": str(uuid.uuid4())[:8],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": level,
                "message": message,
            }
        )
        # 최대 500개까지만 저장
        if len(LOGS) > 500:
            LOGS.pop(0)


# Custom stdout으로 로그를 가로채서 저장
class LogCapture:
    def write(self, message):
        if message.strip():
            add_log("INFO", message.strip())

    def flush(self):
        pass


# 로그 캡처 시작
import sys

original_stdout = sys.stdout
sys.stdout = LogCapture()


@app.get("/")
def read_root():
    add_log("INFO", "서버 접근됨")
    return {"msg": "✅ 백엔드 봇 서버가 정상적으로 동작 중입니다!"}


@app.post("/start")
async def start_bot(req: StartRequest):
    if BOT_STATUS["running"]:
        return {"status": "error", "msg": "봇이 이미 데몬으로 돌고 있습니다!"}

    BOT_STATUS["running"] = True
    BOT_STATUS["interval"] = req.interval_minutes

    # 백그라운드로 봇 실행
    threading.Thread(
        target=run_tennis_bot, args=(req.interval_minutes,), daemon=True
    ).start()

    print(f"🚀 웹에서 시작 요청 받음! 주기: {req.interval_minutes}분")
    return {
        "status": "success",
        "msg": f"테니스 예약 봇이 {req.interval_minutes}분 주기로 가동을 시작했습니다!",
    }


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


@app.get("/logs")
def get_logs(limit: int = 100):
    """최근 로그를 반환하는 엔드포인트"""
    with LOG_LOCK:
        return {"logs": LOGS[-limit:]}
