import asyncio
import time
import os
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

# 실제 운영 시 환경 변수나 .env 파일에서 불러오도록 변경하세요.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "439484740:AAGfGbl5auRZx76fApIJdR59dg9QsteBMbs")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "54702802")

# 중지 신호를 받는 전역 변수
stop_event = asyncio.Event()

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_USER_ID, "text": message})
    except:
        pass

def send_telegram_photo(file_path, caption=""):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(file_path, 'rb') as photo:
            requests.post(url, data={"chat_id": TELEGRAM_USER_ID, "caption": caption}, files={"photo": photo})
    except Exception as e:
        print(f"사진 전송 오류: {e}")

def get_headless_driver():
    """서버 백그라운드 구동을 위한 Headless 크롬 세팅"""
    chrome_options = Options()
    
    # 서버 필수 옵션 (화면 없음, 보안 샌드박스 비활성화)
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # 봇 탐지 우회
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Render.com 같은 서버는 기본 드라이버 이용 가능 (또는 경로 명시 필요)
    driver = webdriver.Chrome(options=chrome_options)
    return driver

async def login_and_wait(driver):
    """용인시 테니스장 접속 후 PASS 앱 간편인증 창 띄우기"""
    URL = "https://publicsports.yongin.go.kr/publicsports/sports/index.do"
    wait = WebDriverWait(driver, 15)
    
    driver.get(URL)
    await asyncio.sleep(2)
    
    try:
        # 1. 개인로그인 클릭
        personal_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@id='GNB_LOGIN_ANCHOR' and contains(@href, 'groupYn=N')]")))
        personal_login.click()
        await asyncio.sleep(1)

        # 2. 휴대폰 인증 리스트 클릭
        phone_auth = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'휴대폰 인증') or contains(text(),'휴대폰인증')]")))
        phone_auth.click()
        await asyncio.sleep(1)

        # 3. 팝업 창 전환
        main_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                break
        
        wait = WebDriverWait(driver, 10)
        
        # 4. KT 알뜰폰 선택 (기존 로직 유지)
        kt_mvno = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick,'KTM')]")))
        driver.execute_script("arguments[0].click();", kt_mvno)
        await asyncio.sleep(1)

        # 5. 간편인증/QR인증 클릭
        qr_auth = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'QR코드 인증') or contains(text(),'간편인증')]")))
        qr_auth.click()

        # 6. 필수 이용 동의 체크 후 다음
        agree_chk = wait.until(EC.presence_of_element_located((By.ID, "check_txt")))
        driver.execute_script("arguments[0].click();", agree_chk)
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='다음'] | //a[text()='다음'] | //input[@value='다음']")))
        next_btn.click()
        await asyncio.sleep(3)

        # 7. 여기서 서버 화면이 없으므로, 현재 모달 페이지 영역의 글자를 모두 가져옵니다.
        # 숫자 7자리(PC 인증번호)를 뽑거나, 전체 스크린샷찰칵 찍습니다!
        screenshot_path = "auth_screen.png"
        driver.save_screenshot(screenshot_path)
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # 7자리 숫자 뽑기 
        # (PASS 앱 화면에 '123 4567' 또는 '1234567' 처럼 나오는 것을 정규식으로 찾기)
        numbers = re.findall(r'\b\d{3}\s?\d{4}\b', page_text)
        auth_number_msg = ""
        if numbers:
            auth_number_msg = f"📱 **PC 인증번호 7자리**: {numbers[0]}"
        else:
            auth_number_msg = "⚠️ 숫자를 자동으로 찾을 수 없습니다. 전송된 사진(스크린샷)에서 확인해 주세요!"

        # 텔레그램으로 메세지 및 사진 발송
        req_msg = f"🔔 서버에서 로그인 창이 열렸습니다!\n\n{auth_number_msg}\n\n스마트폰 PASS 앱에서 인증을 완료하세요 (2분 대기합니다)."
        send_telegram_msg(req_msg)
        send_telegram_photo(screenshot_path, "해당 화면의 인증번호를 PASS 앱에 입력하세요!")
        
        # 사용자가 스마트폰으로 인증할 때까지 충분히 기다림 (120초)
        print("서버: 스마트폰 앱 인증을 대기합니다 (120초)...")
        for _ in range(24): # 5초 * 24 = 120초
            if stop_event.is_set():
                break
            await asyncio.sleep(5)
            # 완료되어 창이 닫혔거나 원래 메인 윈도우로 돌아간 경우 감지 가능하지만, 
            # 단순화를 위해 일단 충분히 기다린 후 팝업 윈도우를 닫고 메인으로 돌아갑니다.

        try:
            driver.switch_to.window(main_window)
            driver.refresh()
            await asyncio.sleep(2)
        except:
            pass
        
        send_telegram_msg("✅ 인증 시간이 종료되어 메인 매크로 모니터링을 시작합니다.")
        return True

    except Exception as e:
        send_telegram_msg(f"❌ 로그인 과정 중 오류 발생:\n{e}")
        return False

async def main_macro_loop(driver, interval_minutes: int):
    """무한 반복 매크로 모니터링 로직"""
    status_msg = f"🚀 테니스장 매크로 감시 시작 (주기: {interval_minutes}분)"
    send_telegram_msg(status_msg)
    print(status_msg)
    
    while not stop_event.is_set():
        # TODO: 기존 main.py의 크롤링 및 예약(perform_reservation) 로직을 그대로 여기에 넣으면 됩니다!
        # 임시로 더미 실행
        print(f"서버: 매크로 감시 1회 실행 중... (다음 실행까지 {interval_minutes}분 대기)")
        
        # 사용자님 기존 로직인 extract_available_slots() 등을 호출합니다.
        
        # 대기 수행 (중지 신호 들어오면 즉시 깨어나도록 쪼개서 대기)
        for _ in range(interval_minutes * 6): 
            if stop_event.is_set():
                break
            await asyncio.sleep(10)

async def run_tennis_bot(interval_minutes: int):
    stop_event.clear()
    driver = None
    try:
        driver = get_headless_driver()
        
        # 로그인 단계 (인증번호 텔레그램 전송 포함)
        login_success = await login_and_wait(driver)
        
        # 무한 매크로 시작
        if login_success and not stop_event.is_set():
            await main_macro_loop(driver, interval_minutes)

    except Exception as e:
        print(f"매크로 서버 에러: {e}")
    finally:
        if driver:
            driver.quit()
        stop_event.clear()
        print("🛑 봇 스크립트 완전 종료")

def stop_tennis_bot():
    stop_event.set()
