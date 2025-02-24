from flask import Flask, render_template, request, redirect, url_for, session, jsonify, current_app
import threading
from selenium import webdriver
import pandas as pd
import shutil
import os
import math
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
import requests
import platform
import webbrowser
from bs4 import BeautifulSoup
import json
import re
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities



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
            EC.presence_of_element_located((By.CLASS_NAME, popup_class))
        )
        
        # 팝업 내부의 버튼 찾기
        confirm_button = popup.find_element(By.XPATH, f".//button[span[text()='{button_text}']]")
        confirm_button.click()
        print("✅ 확인 버튼 클릭 성공")
        return True

    except Exception as e:
        print(f"❌ 팝업 처리 실패: {e}")
        return False

def login_to_site(driver, username, password, login_button_class="header-login-idcr", username_field_id="idModel", password_field_id="pwModel", submit_button_class="btn-login", user_confirm_class="user-nm", wait_time=3):
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
        login_button.click()

        print("✅ 로그인 필드 로드 대기")
        # 사용자 아이디 및 비밀번호 필드 대기
        username_field = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, username_field_id))
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

        # 로그인 성공 확인
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CLASS_NAME, user_confirm_class))
        )
        print("✅ 로그인 성공!")
        return True

    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        return False

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

def extract_table_headers(driver, table_selector):
    try:
         # 테이블 요소 찾기
        table_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
        )
        # 테이블 헤더(날짜 등) 추출
        header_row = table_element.find_elements(By.CSS_SELECTOR, "thead tr th")
        headers = [th.find_element(By.TAG_NAME, "span").text.strip()for th in header_row if th.find_element(By.TAG_NAME, "span").text.strip()]
        print("Headers:", headers)
        return headers  # 성공 시 헤더 반환
    except Exception as e:
        print(f"테이블 헤더 추출 중 오류 발생")
        return None
    
def navigate_to_financial_page(driver, search_key, wait_time=10):
    """
    특정 검색어로 기업을 검색하고, 해당 기업의 재무 페이지로 이동하는 함수.
    """

    try:
        # 검색 필드 요소 찾기
        search_input = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='검색어를 입력해주세요.']"))
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
        return False

            
    # 요소 탐색 및 클릭
    li_index = 1
    found = False

    while True:
        try:
            # 기업명으로 찾기
            name_xpath = f"//*[@id='et-area']/div/div[2]/ul/li[{li_index}]/div/button/span"
            # 사업자번호로 찾기
            code_xpath = f"//*[@id='et-area']/div/div[2]/ul/li[{li_index}]/div/ul[1]/li[4]/span[2]"
            span_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, code_xpath))
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

def setup_user_data():
    if not os.path.exists(COPIED_USER_DATA_DIR):
        print("사용자 데이터 디렉토리 복사 중...")
        shutil.copytree(USER_DATA_DIR, COPIED_USER_DATA_DIR)
        print("복사 완료:", COPIED_USER_DATA_DIR)
    #else:
    #    shutil.rmtree(COPIED_USER_DATA_DIR)
    #    shutil.copytree(USER_DATA_DIR, COPIED_USER_DATA_DIR) 
    #    print("디렉토리 업데이트:", COPIED_USER_DATA_DIR)

# Selenium WebDriver 실행
search_text =""
selenium_running = False
machine = []
sonik =[]
jejo = []
pogwal = []

def run_selenium(username, password, search_key):
    driver = None
    
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
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # DevTools 네트워크 로깅 활성화
            

            #driver 실행
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            # 사이트 이동 및 기업의 재무 페이지로 이동
            driver.get("https://www.cretop.com")
            driver.maximize_window()
            driver.execute_script("document.body.style.zoom='50%'")
            print("사이트 접속 완료")
            driver.implicitly_wait(1)

            # 팝업 처리 
            if handle_popup(driver, popup_class="slot__right", button_text="[닫기]"):
                print("팝업 처리가 완료되었습니다.")
            else:
                print("팝업 처리가 실패했습니다.")

            if login_to_site(driver, username, password):
                
                print("로그인이 성공적으로 완료되었습니다!")
            else:
                print("로그인에 실패했습니다.")

            
            # 로그인 확인 버튼 닫기 _ 팝업 처리 함수 
            if handle_popup(driver):
                print("팝업 처리가 완료되었습니다.")
            else:
                print("팝업 처리가 실패했습니다.")

            time.sleep(1)
           
            s = requests.Session()
            headers = {
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                'Referer': driver.current_url,
                'Origin': 'https://www.cretop.com',
                'Content-Type': 'application/json'
            }
            s.headers.update(headers)
            for cookie in driver.get_cookies():
                c = {cookie['name'] : cookie['value']}
                s.cookies.update(c)
                       
            global search_text, machine, sonik, jejo, pogwal

            if navigate_to_financial_page(driver, search_key):
                print(f"🚀 '{search_key}'의 재무 페이지로 성공적으로 이동했습니다.")
                time.sleep(1)

                strong_element = driver.find_element(By.XPATH, '//*[@id="etfi110m1"]/div/div[2]/div/div/div/div[2]/div/strong')
                search_text = strong_element.text.strip()
                print(search_text)              
            else:
                print(f"❌ '{search_key}'의 재무 페이지로 이동 실패.")


            driver.execute_cdp_cmd("Network.enable", {})
            # :white_check_mark: DevTools 로그에서 네트워크 요청 가져오기
            logs = driver.get_log("performance")

            # `request.json` 요청을 추적하여 `requestId` 저장
            request_id_map = {}

            for log in logs:
                try:
                    log_json = json.loads(log["message"])  # :white_check_mark: JSON 변환
                    method = log_json["message"].get("method", "")

                    # 네트워크 요청이 비동기 처리되거나 fetch()로 이루어진 경우, responseReceived에서만 확인 가능
                    if method == "Network.responseReceived":
                        request_id = log_json["message"]["params"]["requestId"]
                        request_id_map[request_id] = log_json["message"]["params"]
                except (json.JSONDecodeError, KeyError):
                    continue
            # :white_check_mark: 가장 최신 requestId만 사용
            if not request_id_map:
                print(":x: `requestId`를 찾지 못했습니다.")
                driver.quit()
                exit()

            last_request_id = list(request_id_map.keys())[-1]  # :white_check_mark: 가장 마지막 requestId 선택

            # :white_check_mark: `Network.getResponseBody`로 응답 데이터 가져오기 (한 개만 실행)
            try:
                time.sleep(1)  # :white_check_mark: 요청 처리 대기 (빠른 응답 사라짐 방지)
                
                response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": last_request_id})

                # :white_check_mark: 응답이 비어있는 경우 제외
                if not response_body or not response_body.get("body"):
                    print(f"{last_request_id} 응답이 비어 있음")
                else:
                    payload = json.loads(response_body["body"])  # :white_check_mark: 응답 데이터를 JSON 변환

                    # :white_check_mark: `kedcd` 값 추출
                    kedcd = payload.get("header", {}).get("kedcd")
                    if kedcd:
                        print(f"kedcd 값 : {kedcd}")

            except (json.JSONDecodeError, KeyError, Exception) as e:
                print(f":x: {last_request_id} 응답 가져오기 실패: {e}")


            # Chrome 종료
            #driver.quit()
            
            #기계장치(2019~2023)
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
                    "acctDt": "20231231",
                    "fsCcd": "1",
                    "fsCls": "2",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"         Machinery and Equipment"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values1 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("기계장치(2019~2023):", values1)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values1 = []

            #기계장치(2018~2022)
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
                    "acctDt": "20221231",
                    "fsCcd": "1",
                    "fsCls": "2",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"         Machinery and Equipment"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values2 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("기계장치(2018~2022):", values2)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values2 = []
                     
            #손익계산서(2019~2023)
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
                    "acctDt": "20231231",
                    "fsCcd": "2",
                    "fsCls": "2",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"      Employee Salaries and Wages"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values3 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("손익계산서(2019~2023):", values3)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values3 = []

            #손익계산서(2018~2022)
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
                    "acctDt": "20221231",
                    "fsCcd": "2",
                    "fsCls": "2",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"      Employee Salaries and Wages"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values4 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("손익계산서(2018~2022):", values4)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values4 = []

            #제조원가명세서(2019~2023)
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
                    "acctDt": "20231231",
                    "fsCcd": "5",
                    "fsCls": "2",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"      Salaries and Wages"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values5 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("제조원가명세서(2019~2023):", values5)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values5 = []

            #제조원가명세서(2018~2022)
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
                    "acctDt": "20221231",
                    "fsCcd": "5",
                    "fsCls": "2",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }

            url = 'https://www.cretop.com/httpService/request.json'
                       
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"      Salaries and Wages"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values6 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("제조원가명세서(2018~2022):", values6)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values6 = []

            #포괄손익계산서(2019~2023)
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
                    "acctDt": "20231231",
                    "fsCcd": "2",
                    "fsCls": "1",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"   Employee benefits Expenses"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values7 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("포괄손익계산서(2019~2023):", values7)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values7 = []

            #포괄손익계산서(2018~2022)
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
                    "acctDt": "20221231",
                    "fsCcd": "2",
                    "fsCls": "1",
                    "chk": "1",
                    "smryYn": "N",
                    "srchCls": "5"
                }
            }


            url = 'https://www.cretop.com/httpService/request.json'
            
            
            response = s.post(url, json=data, headers=headers)

            response_text = response.text
            pattern = r'\{[^}]*"accNmEng"\s*:\s*"   Employee benefits Expenses"[^}]*\}'
            # 정규 표현식으로 매칭된 모든 부분 찾기
            matches = re.findall(pattern, response_text)
            if matches:
                # 추출된 match에서 val1, val2, val3, val4, val5만 리스트로 추출
                for match in matches:
                    # JSON으로 파싱
                    match_data = json.loads(match)  # 'null'을 Python의 None으로 변환

                    # 원하는 값들만 리스트로 추출
                    values8 = [
                        match_data.get('val1'),
                        match_data.get('val2'),
                        match_data.get('val3'),
                        match_data.get('val4'),
                        match_data.get('val5')
                    ]
                    #print("포괄손익계산서(2018~2022):", values8)
            else:
                print("해당 데이터를 찾을 수 없습니다.")
                values8 = []
           
            inserted_value = values2[0] if values2 else None
            values1.insert(0, inserted_value)
            machine = values1 
            inserted_value = values4[0] if values4 else None
            values3.insert(0, inserted_value)
            sonik = values3 
            inserted_value = values6[0] if values6 else None
            values5.insert(0, inserted_value)
            jejo = values5 
            inserted_value = values8[0] if values8 else None
            values7.insert(0, inserted_value)
            pogwal = values7

            print("재무상태표-기계장치(2018 ~ 2023) :" ,machine)
            print("포괄손익계산서-종업원 급여비용(2018 ~ 2023) :" , pogwal)
            print("손익계산서-직원급여(2018 ~ 2023) :" ,sonik)
            print("제조원가명세서-급여(2018 ~ 2023) :" ,jejo)
           
    except Exception as e:
        print(f"예외 발생: {e}")

    finally:
        # 드라이버 종료가 확실히 호출되도록 함
        if driver:
            driver.execute_script("document.body.style.zoom='100%'")
            driver.quit()
        session['selenium_running'] = False  # 작업 완료 상태로 설정

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        search_key = request.form["search_key"]
        

        run_selenium(username, password, search_key)
        session['selenium_running'] = True  # 세션 유지 설정
        open_browser2()
        return redirect(url_for('calculate'))
    
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
            return float('nan')
        return float(value.replace(',', '').strip())
    return value


@app.route('/calculate', methods=['GET'])
def calculate():
   
    start_year = 2019
    years = list(range(2018, 2024))
    machine_costs = dict(zip(years, machine))
    pogwal_salary = dict(zip(years, pogwal))
    sonik_salary = dict(zip(years, sonik))
    jejo_salary = dict(zip(years, jejo))

    
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
    return render_template('result.html', results=results, totals=totals, company_name=company_name, start_year=start_year)


  # 웹 브라우저 자동 실행 함수
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")  # 기본 페이지 자동 오픈

def open_browser2():
    webbrowser.open("http://127.0.0.1:5000/calculate") 


if __name__ == '__main__':
    # 스레드를 사용하여 웹 브라우저 실행 (서버와 동시에 실행)
    threading.Timer(0.5, open_browser).start()  # 서버 실행 후 1.25초 후 실행
    app.run(debug=True, use_reloader=False)
    
