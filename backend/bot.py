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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()

# 실제 운영 시 환경 변수나 .env 파일에서 불러오도록 변경하세요.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "439484740:AAGfGbl5auRZx76fApIJdR59dg9QsteBMbs")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "54702802")

# 중지 신호를 받는 전역 변수
stop_event = asyncio.Event()

# 전역 설정
TENNIS_COURTS = {
    11715: "기흥 테니스장(B코트)_03월",
    11716: "기흥 테니스장(A코트)_03월",
    12081: "남산근린공원 테니스장(B코트)_04월",
    12082: "남산근린공원 테니스장(A코트)_04월",
    12083: "기흥 테니스장(D코트)_04월",
    12084: "기흥 테니스장(B코트)_04월",
    12085: "기흥 테니스장(A코트)_04월",
}

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_USER_ID, "text": message})
        print(f"\n📱 텔레그램 발송: {message}")
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
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.page_load_strategy = 'eager'
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(3)
    return driver

# ----------------- 예약 관련 유틸 함수 시작 -----------------
def navigate_to_reservation_page(driver, resve_id):
    try:
        url = f"https://publicsports.yongin.go.kr/publicsports/sports/selectFcltyRceptResveApplyListU.do?key=4292&searchResveId={resve_id}"
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return True
    except:
        return False

def extract_available_dates(driver):
    try:
        available_dates = set()
        calendar_cells = driver.find_elements(By.XPATH, "//td[contains(text(), '가능')]")
        for cell in calendar_cells:
            text = cell.text.strip()
            numbers = re.findall(r'\b(\d{1,2})\b', text)
            for num in numbers:
                date_num = int(num)
                if 1 <= date_num <= 31:
                    available_dates.add(date_num)
                    break
        if available_dates:
            return sorted(list(available_dates))
            
        clickable_dates = driver.find_elements(By.CSS_SELECTOR, "a[onclick], button[onclick]")
        for element in clickable_dates[:20]:
            onclick_attr = element.get_attribute('onclick') or ''
            if '예약' in onclick_attr or 'resve' in onclick_attr.lower():
                text = element.text.strip()
                numbers = re.findall(r'\b(\d{1,2})\b', text)
                for num in numbers:
                    date_num = int(num)
                    if 1 <= date_num <= 31:
                        available_dates.add(date_num)
        if available_dates:
            return sorted(list(available_dates))
            
        all_tds = driver.find_elements(By.TAG_NAME, "td")
        for cell in all_tds:
            text = cell.text.strip()
            if any(kw in text for kw in ['접수가능', '예약가능', '신청가능']):
                numbers = re.findall(r'\b(\d{1,2})\b', text)
                for num in numbers:
                    date_num = int(num)
                    if 1 <= date_num <= 31:
                        available_dates.add(date_num)
                        break
        return sorted(list(available_dates)) if available_dates else None
    except:
        return None

def activate_time_selection(driver):
    try:
        cal_content_button = driver.find_element(By.ID, "calContent")
        if 'active' not in (cal_content_button.get_attribute('class') or ''):
            cal_content_button.click()
            time.sleep(1)
        return True
    except:
        return False

def click_date_and_extract_times(driver, date_num):
    try:
        all_tds = driver.find_elements(By.TAG_NAME, "td")
        for td in all_tds:
            text = td.text.strip()
            numbers = re.findall(r'\b(\d{1,2})\b', text)
            if str(date_num) in numbers and any(kw in text for kw in ['접수가능', '예약가능', '신청가능', '가능']):
                td.click()
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.time_cell")))
                except TimeoutException:
                    pass
                time_buttons = driver.find_elements(By.CSS_SELECTOR, "button.time_cell")
                available_times = []
                for btn in time_buttons:
                    caltime = btn.get_attribute('caltime')
                    time_value = caltime if caltime else btn.text.strip()
                    if time_value:
                        available_times.append(time_value)
                return available_times if available_times else None
        return None
    except:
        return None

def extract_available_slots(driver):
    try:
        if not activate_time_selection(driver):
            return None
        available_dates = extract_available_dates(driver)
        if not available_dates:
            return None
        slots = {}
        for date_num in available_dates:
            try:
                times = click_date_and_extract_times(driver, date_num)
                if times:
                    slots[date_num] = times
            except:
                pass
        return slots if slots else None
    except:
        return None

def solve_captcha(driver):
    try:
        captcha_img_div = driver.find_element(By.ID, "image")
        captcha_text = re.sub(r'\s+', '', captcha_img_div.text.strip())
        if captcha_text:
            return captcha_text
        return None
    except:
        return None

def is_target_time(weekday, time_str):
    time_str = time_str.strip()
    if weekday == 5:
        return any(time_str.startswith(f"{hour:02d}") for hour in [6, 7])
    elif weekday == 6:
        return any(time_str.startswith(f"{hour:02d}") for hour in [15, 16, 17, 18])
    return False

def get_year_month_from_court(court_name, current_date):
    match = re.search(r'_(\d{2})월', court_name)
    if match:
        target_month = int(match.group(1))
        target_year = current_date.year
        if current_date.month == 12 and target_month == 1:
            target_year += 1
        elif current_date.month == 1 and target_month == 12:
            target_year -= 1
        return target_year, target_month
    return current_date.year, current_date.month

def perform_reservation(driver, resve_id, date_num, court_name, target_times):
    try:
        print(f"\n🚀 {date_num}일 예약 프로세스 시작")
        if not navigate_to_reservation_page(driver, resve_id):
            return False
            
        if not activate_time_selection(driver):
            return False
            
        available_times = click_date_and_extract_times(driver, date_num)
        if not available_times:
            return False
            
        time_buttons = driver.find_elements(By.CSS_SELECTOR, "button.time_cell")
        matched_button = None
        selected_time = None
        for btn in time_buttons:
            time_value = btn.get_attribute('caltime') or btn.text.strip()
            if time_value in target_times:
                matched_button = btn
                selected_time = time_value
                break
                
        if matched_button:
            matched_button.click()
            time.sleep(0.5)
        else:
            return False

        try:
            next_step_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'btn type4') and contains(text(), '다음단계')]")
            driver.execute_script("arguments[0].click();", next_step_btn)
            time.sleep(2)
        except:
            return False

        try:
            agree_checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for chk in agree_checkboxes:
                if not chk.is_selected():
                    driver.execute_script("arguments[0].click();", chk)
        except:
            return False
        
        try:
            purpose_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "purposeOfUse")))
            purpose_input.clear()
            purpose_input.send_keys("테니스 연습")
        except:
            return False

        captcha_success = False
        for _ in range(5):
            try:
                captcha_code = solve_captcha(driver)
                if captcha_code:
                    captcha_input = driver.find_element(By.ID, "captcha")
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_code)
                    time.sleep(0.5)
                    
                    submit_btn = driver.find_element(By.ID, "registSubmit")
                    driver.execute_script("arguments[0].click();", submit_btn)
                    
                    try:
                        WebDriverWait(driver, 10).until(EC.alert_is_present())
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        if "등록 하시겠습니까" in alert_text or "예약신청" in alert_text:
                            alert.accept()
                            time.sleep(2) 
                            WebDriverWait(driver, 15).until(EC.alert_is_present())
                            alert2 = driver.switch_to.alert
                            if "완료" in alert2.text or "성공" in alert2.text:
                                alert2.accept()
                                captcha_success = True
                                break
                            else:
                                alert2.accept()
                        else:
                            alert.accept()
                    except:
                        try:
                            driver.switch_to.alert.accept()
                        except: pass
            except:
                try:
                    refresh_btn = driver.find_element(By.XPATH, "//button[contains(@onclick, 'generateCaptcha')]")
                    refresh_btn.click()
                except: pass
                time.sleep(1)

        if not captcha_success:
            return False

        msg = f"🎊 [예약 완료!]\n📍 장소: {court_name}\n📅 날짜: {date_num}일\n⏰ 시간: {selected_time}\n서버 자동 예약이 완료되었습니다. 마이페이지에서 확인해 주세요!"
        send_telegram_msg(msg)
        return True

    except Exception as e:
        print(f"❌ 예약 예외 오류: {e}")
        return False
# -----------------------------------------------------

async def login_and_wait(driver):
    """용인시 테니스장 접속 후 PASS 앱 간편인증 창 띄우기"""
    URL = "https://publicsports.yongin.go.kr/publicsports/sports/index.do"
    wait = WebDriverWait(driver, 15)
    
    driver.get(URL)
    await asyncio.sleep(2)
    
    try:
        # 로그인 진행 로직
        personal_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@id='GNB_LOGIN_ANCHOR' and contains(@href, 'groupYn=N')]")))
        personal_login.click()
        await asyncio.sleep(1)

        phone_auth = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'휴대폰 인증') or contains(text(),'휴대폰인증')]")))
        phone_auth.click()
        await asyncio.sleep(1)

        main_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                break
        
        wait = WebDriverWait(driver, 10)
        kt_mvno = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick,'KTM')]")))
        driver.execute_script("arguments[0].click();", kt_mvno)
        await asyncio.sleep(1)

        qr_auth = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'QR코드 인증') or contains(text(),'간편인증')]")))
        qr_auth.click()

        agree_chk = wait.until(EC.presence_of_element_located((By.ID, "check_txt")))
        driver.execute_script("arguments[0].click();", agree_chk)
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='다음'] | //a[text()='다음'] | //input[@value='다음']")))
        next_btn.click()
        await asyncio.sleep(3)

        # 캡처 저장 후 전송
        screenshot_path = "auth_screen.png"
        driver.save_screenshot(screenshot_path)
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        numbers = re.findall(r'\b\d{3}\s?\d{4}\b', page_text)
        auth_number_msg = f"📱 **PC 인증번호 7자리**: {numbers[0]}" if numbers else "⚠️ 숫자를 찾을 수 없습니다. 사진을 확인해 주세요."

        req_msg = f"🔔 서버에서 로그인 창이 열렸습니다!\n\n{auth_number_msg}\n\n스마트폰 PASS 앱에서 인증을 완료하세요 (2분 대기합니다)."
        send_telegram_msg(req_msg)
        send_telegram_photo(screenshot_path, "해당 화면의 인증번호를 PASS 앱에 입력하세요!")
        
        print("서버: 스마트폰 앱 인증을 대기합니다 (120초)...")
        for _ in range(24): 
            if stop_event.is_set():
                break
            await asyncio.sleep(5)

        try:
            driver.switch_to.window(main_window)
            driver.refresh()
            await asyncio.sleep(2)
        except:
            pass
        
        send_telegram_msg("✅ 앱 접속 및 로그인 절차가 마무리되어 메인 감시 루프를 시작합니다.")
        return True

    except Exception as e:
        send_telegram_msg(f"❌ 로그인 과정 중 오류 발생:\n{e}")
        return False

async def main_macro_loop(driver, interval_minutes: int):
    """무한 반복 매크로 모니터링 로직"""
    status_msg = f"🚀 실전 예약 매크로 감시 시작 (주기: {interval_minutes}분)"
    print(status_msg)
    
    while not stop_event.is_set():
        now = datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] 예약 가능 슬롯 확인 중...")
        
        all_available_slots = []
        for resve_id, court_name in TENNIS_COURTS.items():
            if stop_event.is_set(): break
            
            print(f"🔎 {court_name} 확인 중...", flush=True)
            if navigate_to_reservation_page(driver, resve_id):
                available_slots = extract_available_slots(driver)
                if available_slots:
                    for d_num, t_list in available_slots.items():
                        print(f"   📅 {d_num}일: {', '.join(t_list)}")
                        
                    for date_num, times in available_slots.items():
                        try:
                            t_year, t_month = get_year_month_from_court(court_name, now)
                            date_obj = datetime(t_year, t_month, date_num)
                            if date_obj.weekday() >= 5:
                                filtered_times = [t for t in times if is_target_time(date_obj.weekday(), t)]
                                if filtered_times:
                                    all_available_slots.append({
                                        'resve_id': resve_id,
                                        'court_name': court_name,
                                        'date_num': date_num,
                                        'times': filtered_times
                                    })
                        except:
                            continue
                await asyncio.sleep(0.5)

        found_reservation = False
        if all_available_slots:
            all_available_slots.sort(key=lambda x: x['date_num'])
            found_msg = f"✨ 총 {len(all_available_slots)}개의 예약 가능 주말 슬롯 발견. 바로 캡차 예약을 시도합니다!"
            send_telegram_msg(found_msg)
            print(found_msg)
            
            for slot in all_available_slots:
                if stop_event.is_set(): break
                if perform_reservation(driver, slot['resve_id'], slot['date_num'], slot['court_name'], slot['times']):
                    found_reservation = True
                    break
        
        if not found_reservation:
            wait_msg = f"ℹ️ 완료: 예약 가능한 주말 타겟 슬롯이 없습니다. (다음 스캔까지 {interval_minutes}분 대기)"
            print(wait_msg)
            # 텔레그램으로도 조용히 생존 신고 날리기
            send_telegram_msg(f"🤖 [생존 안내] 1회 스캔 완료 / 주말 겟(Get) 대상 없음 / 정상 감시 중...👀")

        # 대기 시간 (interval) 쪼개서 대기
        for _ in range(interval_minutes * 6): 
            if stop_event.is_set():
                break
            await asyncio.sleep(10)

async def run_tennis_bot(interval_minutes: int):
    stop_event.clear()
    driver = None
    try:
        driver = get_headless_driver()
        login_success = await login_and_wait(driver)
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
