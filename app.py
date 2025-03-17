from flask import Flask, render_template, request, redirect, url_for, session, jsonify, current_app
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import requests
import platform
import webbrowser
import json
import threading
import pandas as pd
import shutil
import os
import math
import re


def handle_popup(driver, popup_class="pop-alert", button_text="확인", wait_time=5):
    """
    팝업 확인 및 버튼 클릭 함수.

    Args:
        driver: Selenium WebDriver 객체.
        popup_class (str): 팝업의 클래스 이름. 기본값은 "pop-alert".
        button_text (str): 버튼의 텍스트. 기본값은 "확인".
        wait_time (int): 대기 시간 (초). 기본값은 5초.

    Returns:
        bool: 버튼 클릭 성공 여부.
    """
    try:
        
        # 팝업 요소 찾기
        popup = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.CLASS_NAME, popup_class))
        )
        
        # 팝업 내부의 버튼 찾기
        confirm_button = popup.find_element(By.XPATH, f".//button[span[text()='{button_text}']]")
        confirm_button.click()
        print("✅ 확인 버튼 클릭 성공")
        return True

    except Exception as e:
        print(f"❌ 팝업 처리 실패: {e}")
        return False

def login_to_site(driver, username, password, login_button_class="header-login-idcr", username_field_id="idModel", password_field_id="pwModel", submit_button_class="btn-login", user_confirm_class="user-nm", wait_time=10):
    """
    사이트 로그인 함수.

    Args:
        driver: Selenium WebDriver 객체.
        username (str): 사용자 아이디.
        password (str): 사용자 비밀번호.
        login_button_class (str): 로그인 버튼의 클래스 이름. 기본값은 "header-login-idcr".
        username_field_id (str): 사용자 아이디 필드의 ID. 기본값은 "idModel".
        password_field_id (str): 비밀번호 필드의 ID. 기본값은 "pwModel".
        submit_button_class (str): 로그인 제출 버튼의 클래스 이름. 기본값은 "btn-login".
        user_confirm_class (str): 로그인 성공 확인 요소의 클래스 이름. 기본값은 "user-nm".
        wait_time (int): 대기 시간 (초). 기본값은 10초.

    Returns:
        bool: 로그인 성공 여부.
    """
    try:
        print("🔍 로그인 버튼 클릭 시도")
        # 로그인 버튼 클릭
        login_button = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.CLASS_NAME, login_button_class))
        )
        #login_button.click()

        # 사용자 아이디 및 비밀번호 필드 대기
        username_field = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.ID, username_field_id))
        )
        password_field = driver.find_element(By.ID, password_field_id)

        # 사용자 아이디 및 비밀번호 입력
        username_field.click() 
        username_field.clear()
        password_field.click()  
        password_field.clear()
        username_field.send_keys(username)
        password_field.send_keys(password)

        print("✅ 로그인 정보 입력 완료")

        # 로그인 제출 버튼 클릭
        submit_button = driver.find_element(By.CLASS_NAME, submit_button_class)
        submit_button.click()
        print("🔍 로그인 버튼 클릭 중...")

        try:
            error_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pop-area"))
            )
            error_text = error_element.get_attribute("class")
            
            with open(UPDATE_TRACKER_FILE, "w") as file:
                file.write("")

            if "PLIL140P5" in error_text:
                print("🚫 동일한 아이디로 다른 디바이스에서 로그인 중입니다. 다른 기기에서 로그아웃해주세요.")
                return False
            elif "PLIL140P4" in error_text:
                print("🚫 접속기기가 변경되었습니다. 크롬을 열어 크레탑 본인인증 후 앱을 재사용해주세요.")
                return False
        except:
            print("로그인 오류 팝업 없음")
            
        # 로그인 성공 확인
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CLASS_NAME, user_confirm_class))
        )
        print("✅ 로그인 성공!")
        time.sleep(1)
        return True

    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        driver.quit()
        os._exit(0)

def click_button_by_text(driver, button_text):
    """
    주어진 텍스트를 포함한 <a> 버튼을 클릭합니다.

    Args:
        driver: Selenium WebDriver 객체.
        button_text: 클릭하고자 하는 버튼의 텍스트.

    Returns:
        None
    """
    try:
        # 텍스트를 기반으로 버튼 찾기
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[span[text()='{button_text}']]"))
        )
        # 클릭
        button.click()
        print(f"'{button_text}' 버튼 클릭 완료")
    except Exception as e:
        print(f"'{button_text}' 버튼 클릭 실패: {e}")
        driver.quit()
        os._exit(0)
  
def navigate_to_financial_page(driver, search_key, wait_time=10):
    """
    특정 검색어로 기업을 검색하고, 해당 기업의 재무 페이지로 이동하는 함수.
    """

    try:
        # 검색 필드 요소 찾기
        search_input = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='검색어를 입력해주세요.']"))
        )
        
        # 검색어 입력
        search_input.clear()
        search_input.send_keys(search_key)

        # 검색 버튼 클릭
        search_button = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='검색하기']"))
        )
        search_button.click()
        print("✅ 검색 버튼 클릭 완료")
        time.sleep(1)

    except Exception as e:
        print(f"❌ 검색 단계 실패: {e}")
        driver.quit()
        os._exit(0)
        return False

            
    # 요소 탐색 및 클릭
    li_index = 1
    found = False

    while True:
        try:
            # 사업자번호로 찾기
            code_xpath = f"//*[@id='et-area']/div/div[2]/ul/li[{li_index}]/div/ul[1]/li[4]/span[2]"
            span_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, code_xpath))
            )
            
            # 찾은 텍스트와 검색어 비교
            if search_key in span_element.text.strip():
                print(f"✅ '{search_key}' 찾음!")
                found = True
                break
            else:
                li_index += 1

        except Exception as e:
            print(f"❌ 찾을 수 있는 항목이 없습니다. (오류: {e})")
            driver.quit()
            os._exit(0)
            break
            
    # 일치하는 항목이 있으면 "재무페이지로 이동하기" 클릭
    if found:
        finance_page_xpath = f"//*[@id='et-area']/div/div[@class='inner__area']/ul/li[{li_index}]/div/ul[@class='btn__list']/li[4]/a"
        finance_page_element = driver.find_element(By.XPATH, finance_page_xpath)
        finance_page_element.click()
        print("재무페이지로 이동 완료")
        return 1
    else:
        print("재무페이지 이동 실패")
        driver.quit()
        os._exit(0)

def get_kedcd(driver): 
    # ✅ DevTools 로그에서 네트워크 요청 가져오기
    logs = driver.get_log("performance")

    # `request.json` 요청을 추적하여 `requestId` 저장
    request_id_map = {}

    for log in logs:
        try:
            log_json = json.loads(log["message"])  
            method = log_json["message"].get("method", "")

            # 네트워크 요청이 비동기 처리되거나 fetch()로 이루어진 경우, responseReceived에서만 확인 가능
            if method == "Network.responseReceived":
                request_id = log_json["message"]["params"]["requestId"]
                request_id_map[request_id] = log_json["message"]["params"]
        except (json.JSONDecodeError, KeyError):
            continue
    # ✅ 가장 최신 requestId만 사용
    if not request_id_map:
        print("❌ `requestId`를 찾지 못했습니다.")
        driver.quit()
        os._exit(0)

    request_ids = list(request_id_map.keys())[::-1]  # 최신 requestId부터 선택

    # ✅ `Network.getResponseBody`로 응답 데이터 가져오기 (한 개만 실행)
    while request_ids:  # ✅ request_ids가 남아있는 동안 반복
            last_request_id = request_ids.pop(0)  # ✅ 가장 최신 requestId 선택
            print(f"✅ 시도 중인 `requestId`: {last_request_id}")

            try:
                time.sleep(1)  # 요청 처리 대기 (빠른 응답 사라짐 방지)

                response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": last_request_id})

                # 응답이 비어있는 경우 제외
                if not response_body or not response_body.get("body"):
                    print(f"`{last_request_id}` 응답이 비어 있음")
                    continue 

                payload = json.loads(response_body["body"])  

                kedcd = payload.get("header", {}).get("kedcd")
                if kedcd:
                    print(f"✅ `kedcd` 값 찾음: {kedcd}")
                    return kedcd  
    
            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f"❌ {last_request_id} 응답 가져오기 실패: {e}")
    driver.quit()
    os._exit(0)

target_tabs = {
    "재무상태표": {"accNmEng": "         Machinery and Equipment", "fsCcd": "1", "fsCls": "2"},
    "포괄손익계산서": {"accNmEng": "   Employee benefits Expenses", "fsCcd": "2", "fsCls": "1"},
    "손익계산서": {"accNmEng": "      Employee Salaries and Wages", "fsCcd": "2", "fsCls": "2"},
    "법인세비용차감전순손익" :  {"accNmEng": "(Ongoing Business) Income or Loss Before Income Taxes Expenses", "fsCcd": "2", "fsCls": "2"},
    "법인세비용" :  {"accNmEng": "Income Taxes Expenses (For Ongoing Business Income or Loss)", "fsCcd": "2", "fsCls": "2"},
    "제조원가명세서": {"accNmEng": "      Salaries and Wages", "fsCcd": "5", "fsCls": "2"},
    "포괄_법인세비용차감전순이익" : {"accNmEng": "Profits(Losses) before Tax", "fsCcd": "2", "fsCls": "1"},
    "포괄_법인세비용": {"accNmEng": "(Income Tax Expenses)", "fsCcd": "2", "fsCls": "1"}
    
}

def get_tabs_values(driver, username, kedcd, session, years):

    headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Referer': driver.current_url,
    'Origin': 'https://www.cretop.com',
    'Content-Type': 'application/json'
}
    url = 'https://www.cretop.com/httpService/request.json'

    values_list = []
    cookies = driver.get_cookies()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    # ✅ 탭 리스트 가져오기
    tabs = driver.find_elements(By.CSS_SELECTOR, "ul.tab-group-ul > li > a")
    existing_tabs = {tab.text.strip() for tab in tabs}

    missing_tabs = set(target_tabs.keys()) - existing_tabs
    all_tabs = set(target_tabs.keys())

    # ✅ '포괄손익계산서'가 없을 경우만 특정 탭 조정 (
    if "포괄손익계산서" in missing_tabs:
        all_tabs.discard("포괄손익계산서")
        values = ["포괄손익계산서"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
        all_tabs.discard("포괄_법인세비용차감전순이익")
        values = ["포괄_법인세비용차감전순이익"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
        all_tabs.discard("포괄_법인세비용")
        values = ["포괄_법인세비용"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
    else: 
        all_tabs.discard("손익계산서")
        values = ["손익계산서"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
        all_tabs.discard("제조원가명세서")
        values = ["제조원가명세서"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
        all_tabs.discard("법인세비용차감순손익")
        values = ["법인세비용차감순손익"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
        all_tabs.discard("법인세비용")
        values = ["법인세비용"] +  [ None for _ in range(1, 7)]
        values_list.append(values)
        

    for tab_name in all_tabs:
        # ✅ 해당 탭의 fsCcd, fsCls 및 accNmEng 가져오기
        tab_data = target_tabs[tab_name]
        accNmEng = tab_data["accNmEng"]
        fsCcd = tab_data["fsCcd"]
        fsCls = tab_data["fsCls"]
        if (years == 2022):
            acctDt = "20221231"
        else:
            acctDt = "20231231"

        # ✅ 요청 데이터 생성 
        data = {
            "header": {
                "trxCd": "ETFI1122R",
                "sysCd": "",
                "chlType": "02",
                "userId": username.upper(),
                "screenId": "ETFI112S2",
                "menuId": "01W0000777",
                "langCd": "ko",
                "bzno": "",
                "conoPid": "",
                "kedcd": kedcd,
                "indCd": "",
                "franMngNo": "",
                "ctrNo": "",
                "bzcCd": "",
                "infoOfrStpgeYn": "",
                "pageNum": 0,
                "pageCount": 0,
                "pndNo": ""
            },
            "ETFI1122R": {
                "kedcd": kedcd,
                "acctCcd": "Y",
                "acctDt": acctDt,
                "fsCcd": fsCcd,  
                "fsCls": fsCls,  
                "chk": "1",
                "smryYn": "N",
                "srchCls": "5"
            }
        }

        # ✅ API 요청 보내기
        response = session.post(url, json=data, headers=headers)
        response_text = response.text

        accNmEng = re.escape(accNmEng)
        normalized_accNmEng = " ".join(tab_data["accNmEng"].split())
        pattern = fr'\{{[^}}]*"accNmEng"\s*:\s*".*?{accNmEng}.*?"[^}}]*\}}'

        matches = re.findall(pattern, response_text)

        if matches:
            for match in matches:
                match_data = json.loads(match) 
                values = [tab_name] + [years] + [match_data.get(f'val{i}') for i in range(1, 6)]
                values_list.append(values)

            print(f"✅ {tab_name} ({normalized_accNmEng}): {values_list[-1]}")
            continue

        else:
            values = [tab_name] +  [ None for _ in range(1, 7)]
            values_list.append(values)
            print(f"❌ {tab_name} 데이터를 찾을 수 없습니다.")

    return values_list if values_list else None  

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_chrome_user_data_dir():
    system = platform.system()
    base_dir = os.path.expanduser("~")

    if system == "Windows":
        return os.path.join(base_dir, "AppData", "Local", "Google", "Chrome", "User Data")
    elif system == "Darwin":  # macOS
        return os.path.join(base_dir, "Library", "Application Support", "Google", "Chrome")
    elif system == "Linux":  # Linux
        return os.path.join(base_dir, ".config", "google-chrome")
    else:
        raise NotImplementedError("이 운영 체제에서는 지원되지 않습니다.")

def get_copied_user_data_dir():
    system = platform.system()
    base_dir = os.path.expanduser("~")

    if system == "Windows":
        return os.path.join(base_dir, "AppData", "Local", "Google", "Chrome_Selenium")
    elif system == "Darwin":  # macOS
        return os.path.join(base_dir, "Library", "Application Support", "Google", "Chrome_Selenium")
    elif system == "Linux":  # Linux
        return os.path.join(base_dir, ".config", "google-chrome-selenium")
    else:
        raise NotImplementedError("이 운영 체제에서는 지원되지 않습니다.")

USER_DATA_DIR = get_chrome_user_data_dir()
COPIED_USER_DATA_DIR = get_copied_user_data_dir()
UPDATE_TRACKER_FILE = "last_update.txt"

def setup_user_data():
    today = datetime.today().strftime("%Y-%m-%d")
    if os.path.exists(UPDATE_TRACKER_FILE):
        with open(UPDATE_TRACKER_FILE, "r") as file:
            last_update = file.read().strip()  #  마지막 업데이트 날짜 읽기
    else:
        last_update = None  # 업데이트 기록이 없으면 None 처리

    # 디렉토리 존재 여부 확인 + 날짜 비교 후 업데이트 여부 결정
    if not os.path.exists(COPIED_USER_DATA_DIR) or last_update != today: 
        print("사용자 데이터 디렉토리 업데이트 중...")
        os.system("taskkill /IM chrome.exe /F") # 윈도우 크롬 강제종료 코드 (하루에 한 번만 실행됨)
        if os.path.exists(COPIED_USER_DATA_DIR):
            shutil.rmtree(COPIED_USER_DATA_DIR)
        shutil.copytree(USER_DATA_DIR, COPIED_USER_DATA_DIR)
        print("디렉토리 복사 완료:", COPIED_USER_DATA_DIR)
        
        with open(UPDATE_TRACKER_FILE, "w") as file:
            file.write(today)
    else: 
        print(" 기존 디렉토리 사용.")

search_text =""
selenium_running = False
kedcd = ""
value_2023 = []
value_2022 = []
machine = []
sonik =[]
jejo = []
pogwal = []
before_loss = []
taxes = []

def run_selenium(username, password, search_key):
    driver = None
    global search_text, kedcd, value_2022, value_2023, machine, sonik, jejo, pogwal,before_loss, taxes

    try:
        with app.test_request_context():

            setup_user_data()

            options = webdriver.ChromeOptions()
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            options.add_experimental_option("detach", True) # 화면 창 닫기 방지
            options.add_argument(f"user-data-dir={COPIED_USER_DATA_DIR}")  # 복사된 프로파일 경로 지정
            options.add_argument("--profile-directory=Default")  # 특정 프로파일 중 default 사용
            options.add_argument("--headless")  # Headless 모드 활성화
            options.add_argument("--disable-autofill")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # DevTools 네트워크 로깅 활성화

            #driver 실행
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            # 사이트 이동 및 기업의 재무 페이지로 이동
            driver.get("https://www.cretop.com")
            driver.maximize_window()
            driver.execute_script("document.body.style.zoom='100%'")
            print("사이트 접속 완료")
            time.sleep(1)

            # 팝업 처리 
            if handle_popup(driver, popup_class="check-close__footer", button_text="[닫기]"):
                print("팝업 처리가 완료되었습니다.")
            else:
                print("팝업 처리가 실패했습니다.")

            if driver.find_elements(By.CSS_SELECTOR, ".login-after"):
                print("로그인 중입니다.")
            else:
                if login_to_site(driver, username, password):
                    print("로그인이 성공적으로 완료되었습니다!")
                else:
                    print("로그인에 실패했습니다.")
                    driver.quit()
                    os._exit(0)

                # 로그인 확인 버튼 닫기 _ 팝업 처리 함수 
                if handle_popup(driver):
                    print("팝업 처리가 완료되었습니다.")
                else:
                    print("팝업 처리가 실패했습니다.")

                time.sleep(1)
           
            session = requests.Session()

            for cookie in driver.get_cookies():
                c = {cookie['name'] : cookie['value']}
                session.cookies.update(c)    

            if navigate_to_financial_page(driver, search_key):
                print(f"🚀 '{search_key}'의 재무 페이지로 성공적으로 이동했습니다.")
                time.sleep(1)

                strong_element = driver.find_element(By.XPATH, '//*[@id="etfi110m1"]/div/div[2]/div/div/div/div[2]/div/strong')
                search_text = strong_element.text.strip()
                print(search_text)              
            else:
                print(f"❌ '{search_key}'의 재무 페이지로 이동 실패.")
                driver.quit()
                os._exit(0)

            driver.execute_cdp_cmd("Network.enable", {})
            kedcd = get_kedcd(driver)

            value_2023 = get_tabs_values(driver, username, kedcd, session, 2023)
            value_2022 = get_tabs_values(driver, username, kedcd, session, 2022)
            
            for row, row_2022 in zip(value_2023, value_2022): # value_2023에 2018 값 삽입
                row[1] = row_2022[2]
            
            for tab in value_2023:
                print(tab)

            for row in value_2023:
                if row[0] == "포괄손익계산서":
                    pogwal = row[1:7] 
                elif row[0] == "손익계산서":
                    sonik = row[1:7] 
                elif row[0] == "제조원가명세서":
                    jejo = row[1:7] 
                elif row[0] == "재무상태표":
                    machine = row[1:7]
                elif row[0] == "법인세비용차감전순손익" and not None:
                    before_loss = row[1:7]
                elif row[0] == "포괄_법인세비용차감전순이익" and not None:
                    before_loss = row[1:7]
                elif row[0] == "법인세비용" and not None:
                    taxes = row[1:7]
                elif row[0] == "포괄_법인세비용" and not None:
                    taxes = row[1:7]


    finally:
        # 드라이버 종료가 확실히 호출되도록 함
        if driver:
            driver.execute_script("document.body.style.zoom='100%'")
            driver.quit()
        # session.get('selenium_running', False)    # 작업 완료 상태로 설정
        # session.modified = True  # 변경 내용 저장

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = session.get("username", request.form["username"])
        password = session.get("password", request.form["password"])
        search_key = request.form["search_key"]

        session["username"] = username
        session["password"] = password
        
        run_selenium(username, password, search_key)
        session['selenium_running'] = True  # 세션 유지 설정

        return jsonify({"redirect": url_for('calculate')})
    
    return render_template("index.html")

@app.route('/selenium_status', methods=['GET'])
def selenium_status():
    status = session.get('selenium_running', False)  # 기본값은 False
    return jsonify({"running": status})

def calculate_yearly_cost(year, machine_costs, pogwal_salary=None, sonik_salary=None, jejo_salary=None, num=7700, avg_rate=0.03, avg_rate_after_2023=0.1):
    if pogwal_salary is None and sonik_salary is None:
        raise ValueError("pogwal_salary와 sonik_salary 중 하나는 반드시 필요합니다.")
    
    prev_year = year - 1
    if machine_costs is None:
        years_available = []
    else:
        years_available = [year - i for i in range(1, 4) if (year - i) in machine_costs]
    prev_3_year_avg = sum((machine_costs.get(year, 0) or 0) for y in years_available) / len(years_available) if years_available else 0

    # 인원 계산
    if pogwal_salary is not None:
        salary_increase = max(0, (pogwal_salary.get(year, 0) or 0) - (pogwal_salary.get(prev_year, 0) or 0))
    elif sonik_salary is not None or jejo_salary is not None:
        sonik_increase = (sonik_salary.get(year, 0) or 0) - (sonik_salary.get(prev_year, 0) or 0) if sonik_salary else 0
        jejo_increase = (jejo_salary.get(year, 0) or 0) - (jejo_salary.get(prev_year, 0) or 0) if jejo_salary else 0
        salary_increase = max(0, sonik_increase + jejo_increase)
    else:
        salary_increase = 0

    salary_adjustment = math.floor(salary_increase / 40000) * num

    # 기계장치 계산
    machine_cost_current = machine_costs.get(year, 0) or 0
    machine_cost_prev = machine_costs.get(prev_year, 0) or 0
    
    if year == 2019:
        machine_cost_total = (machine_cost_current - machine_cost_prev) * 0.07
    elif year == 2020:
        machine_cost_total = (machine_cost_current - machine_cost_prev) * 0.1
    elif year in [2021, 2022]:
        machine_cost_total = (machine_cost_current - machine_cost_prev) * 0.1 + (machine_cost_current - prev_3_year_avg) * avg_rate
    else:  # year >= 2023
        prev_year_cost = (machine_cost_current - machine_cost_prev) * 0.12
        adjusted_cost = (machine_cost_current - prev_3_year_avg) * avg_rate_after_2023
        machine_cost_total = prev_year_cost + min(adjusted_cost, prev_year_cost * 2)

    machine_cost_total = max(machine_cost_total, 0)

    total = machine_cost_total + salary_adjustment
    return machine_cost_total, salary_adjustment, total

def convert_to_numeric(value):
    """문자열을 숫자로 변환하고, '-' 같은 특수문자는 NaN으로 처리"""
    if isinstance(value, str):
        if value.strip() == '-' or value.strip() == '':
            return float('nan')  # ✅ NaN을 float으로 유지
        try:
            return int(value.replace(',', '').strip())
        except ValueError:
            return float('nan') 
    return value  # 이미 숫자면 그대로 반환


@app.route('/calculate', methods=['GET'])
def calculate():
   
    start_year = 2019
    years = list(range(2018, 2024))
    # machine_costs = dict(zip(years, machine))
    # pogwal_salary = dict(zip(years, pogwal))
    # sonik_salary = dict(zip(years, sonik))
    # jejo_salary = dict(zip(years, jejo))

    machine_costs = {year: convert_to_numeric(x) for year, x in zip(years, machine)}
    pogwal_salary = {year: convert_to_numeric(x) for year, x in zip(years, pogwal)}
    sonik_salary = {year: convert_to_numeric(x) for year, x in zip(years, sonik)}
    jejo_salary = {year: convert_to_numeric(x) for year, x in zip(years, jejo)}
    
    if all(value is None for value in pogwal_salary.values()):
        pogwal_salary = None
    if all(value is None for value in sonik_salary.values()):
        sonik_salary = None
    if all(value is None for value in jejo_salary.values()):
        jejo_salary = None

    if not pogwal_salary and not sonik_salary and not jejo_salary:
        return "포괄 급여나 손익/제조 급여가 필요합니다.", 400
    elif not pogwal_salary:
        pogwal_salary = None  # 명시적으로 설정

    results, total_machine_cost, total_salary_adjustment, total_cost = {}, 0, 0, 0

    # 연도별 비용 계산
    for year in range(start_year, start_year + 5):
        try:
            machine_cost_total, salary_adjustment, total = calculate_yearly_cost(
                year, machine_costs, pogwal_salary, sonik_salary, jejo_salary
            )
            results[year] = {"machine_cost_total": round(machine_cost_total),
                             "salary_adjustment": round(salary_adjustment),
                             "total": round(total)}

            total_machine_cost += machine_cost_total
            total_salary_adjustment += salary_adjustment
            total_cost += total

        except KeyError as e:
            results[year] = {"error": f"데이터가 없습니다: {e}"}
        except ValueError as e:
            results[year] = {"error": f"계산 오류: {e}"}

    totals = {"machine_cost_total": round(total_machine_cost),
              "salary_adjustment": round(total_salary_adjustment),
              "total": round(total_cost)}

    company_name = search_text
    return render_template('result.html', results=results, totals=totals, company_name=company_name, start_year=start_year, before_loss=before_loss, taxes=taxes)


@app.route('/rerun', methods=['POST'])
def rerun():
    """검색어만 초기화하고 로그인 페이지로 이동"""
    global driver  # 전역 변수로 관리되는 경우
    
    if 'driver' in globals() and driver is not None:
        try:
            driver.quit()  # Selenium 드라이버 종료
        except Exception as e:
            print(f"드라이버 종료 중 오류 발생: {e}")
        finally:
            driver = None  # 드라이버 객체 초기화
            
    session.pop("search_key", None)  # 기존 검색어만 삭제
    return redirect(url_for('login'))


  # 웹 브라우저 자동 실행 함수
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")  # 기본 페이지 자동 오픈
    
if __name__ == '__main__':
    # 스레드를 사용하여 웹 브라우저 실행 (서버와 동시에 실행)
    threading.Timer(0.5, open_browser).start()  # 서버 실행 후 1.25초 후 실행
    app.run(debug=True, use_reloader=False)
    
