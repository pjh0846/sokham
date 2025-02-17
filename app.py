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
import pickle


def handle_popup(driver, popup_class="pop-alert", button_text="확인", wait_time=20):
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
    
def check_nodata(driver,tab_name):
    try:
        nodata_xpath = "//table[contains(@class, 'details')]//td"

        # Wait for the table cell to appear
        no_data_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.XPATH, nodata_xpath))
        )

        # Check if the element's text matches the expected value
        if no_data_element.text.strip() == '조회된 자료가 없습니다.':
            print("🚨 No Data Found!")
            return True  # 데이터 없음

    except Exception:
        print("✅ Data is available!")
        return False  # 데이터 있음
    
    return False

def extract_row(driver,row_element, wait_time=2):
    """
    테이블에서 발견된 행을 추출하는 함수.

    Returns:
        list: 추출된 첫 번째 행 데이터. (예: ['매출액(*)', '10,180,665', ...])
    """
    try:
        # 'td span' 요소에서 텍스트 추출
        spans = row_element.find_elements(By.CSS_SELECTOR, "td span")
        row_data = [span.text.strip() for span in spans if span.text.strip()]
        print(f"✅ 추출된 데이터: {row_data}")
        return row_data

    except Exception as e:
        print(f"❌행 추출 실패: {e}")
        return []

def find_machine_asset(driver, tab_name):
    # scroll
    before_h = driver.execute_script("return window.scrollY")
    while True:
        # to the bottom
        driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END) # 키보드 END
        time.sleep(1) # loading
        after_h = driver.execute_script("return window.scrollY")
        
        if before_h == after_h:
            break
        before_h = after_h

    try:
        machine_assets = WebDriverWait(driver, 5).until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, "tr.depth-4")
        )

        # `depth-4` 중 기계장치 텍스트가 있는 것 선택
        machine_asset = None
        for asset in machine_assets:
            text = asset.find_element(By.CSS_SELECTOR, "span").text.strip()
            if text == "기계장치":
                machine_asset = asset
                print(f"기계장치 발견: {text}")
                spans = machine_asset.find_elements(By.CSS_SELECTOR, "td span")
                machine_row_data = [tab_name] + [span.text.strip() for span in spans if span.text.strip()]
                print(f"✅ 추출된 machine 데이터: {machine_row_data}")
                return machine_row_data
            else:
                continue
        return [tab_name, '기계장치', '0', '0', '0', '0', '0']
    
    except Exception as e:
        print(f"기계장치 검색 실패 또는 조건 미충족: {e}")
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

def change_range(driver, dropdown_id="range", range_value="5", wait_time=2):
    """
    범위를 변경하는 함수.

    Args:
        driver: Selenium WebDriver 객체.
        dropdown_id (str): 범위 선택 드롭다운의 ID. 기본값은 "range".
        range_value (str): 선택할 범위 값. 기본값은 "5".
        wait_time (int): 대기 시간 (초). 기본값은 2초.

    Returns:
        bool: 범위 변경 성공 여부.
    """
    try:
        # 드롭다운 요소 대기
        dropdown = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, dropdown_id))
        )

        # Select 클래스를 사용하여 범위 변경
        select = Select(dropdown)
        select.select_by_value(range_value)  # 원하는 값 선택
    
        search_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#etfi110m1 .btn-wrap > button"))
        )
        search_button.click()
        print(f"✅ 범위를 '{range_value}'로 성공적으로 변경했습니다.")
        return True

    except Exception as e:
        print(f"❌ 범위 변경 실패: {e}")
        return False

def create_and_save_excel(headers, row_data, tab_name, excel_path):

    """
    DataFrame 생성, tab_name 추가, 엑셀 저장
    
    Parameters:
        headers (list): 데이터 프레임의 컬럼 헤더
        row_data (list): 데이터 프레임에 추가할 행 데이터
        tab_name (str): 현재 탭 이름
        excel_path (str): 저장할 엑셀 파일 경로
    """
    try:
        # 기존 엑셀 파일 읽기 (파일이 없으면 새로 생성)
        try:
            existing_df = pd.read_excel(excel_path, sheet_name='Sheet1', index_col=0)
            print("Existing Excel file loaded successfully.")
        except FileNotFoundError:
            existing_df = pd.DataFrame(columns=[""] + headers)
            print("No existing Excel file. Creating a new one.")
        
        # 새로운 데이터를 데이터프레임으로 생성
        new_row = pd.DataFrame([row_data], columns=headers)
        new_row.insert(0, "", tab_name)  # 첫 번째 열에 tab_name 추가
        print("New row with tab_name added:")
        print(new_row)

        # 기존 데이터프레임과 새로운 데이터 합치기
        combined_df = pd.concat([existing_df, new_row], ignore_index=True)
        print("Combined DataFrame:")
        print(combined_df)

        # 엑셀 저장
        combined_df.to_excel(excel_path, sheet_name='Sheet1', index=False)
        print(f"Data saved successfully to {excel_path}")
    except Exception as e:
        print(f"Error while creating and saving Excel: {e}")

def create_df(total_df, row_data, headers, tab_name):
    if total_df.empty:
        total_df = pd.DataFrame([row_data], columns=headers)
        total_df.insert(0, "", tab_name)
    else:
        total_df.loc[-1] = row_data
        total_df.index = total_df.index+1
        total_df = total_df.sort_index()
        
    print(f"🌱 {tab_name} Combined DataFrame:")
    print(total_df)
    return total_df

def get_2018(driver):
#결산일자 변경해서 2018 값 받아오는 함수
    try:
        # <select> 요소 찾기
        time.sleep(1)
        settlement_date_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "settlement-date"))
        )
        settlement_date_dropdown = Select(settlement_date_select)

        # value="20221231"인 옵션 선택
        settlement_date_dropdown.select_by_value("20221231")

        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.btn-wrap > button.btn.default.w-240.h-56"))
        )

        button.click()
        driver.execute_script("arguments[0].click();", button)
        time.sleep(1)
        print(f"✅ 결산일자를 2022로 성공적으로 변경했습니다.")

    except Exception as e:
        print(f"❌ 결산일자 변경 실패: {e}")

def nodata_df(total_df, tab_name, version = 1):
    # tab_name: non-default arguments must come before default arguments.
    row_data = [tab_name, 'None', '0', '0', '0', '0', '0'] 
    if version == 1:
        if total_df.empty:
            v1_col = ['tab', '계정명', '2019-12-31', '2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31']
            total_df = pd.DataFrame([row_data], columns=v1_col)
        else:
            total_df.loc[-1] = row_data
            total_df.index = total_df.index+1
            total_df = total_df.sort_index()
    else:
        if total_df.empty:
            v2_col = ['tab', '계정명', '2018-12-31', '2019-12-31', '2020-12-31', '2021-12-31', '2022-12-31']
            total_df = pd.DataFrame([row_data], columns= v2_col)
        else:
            total_df.loc[-1] = row_data
            total_df.index = total_df.index+1
            total_df = total_df.sort_index() 

    print("DataFrame for ❌ no ❌ data:")
    print(total_df)
    return total_df
                
def comprehensive(driver, tab_name):
    time.sleep(1)
    # scroll
    before_h = driver.execute_script("return window.scrollY")
    while True:
        # to the bottom
        driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END) 
        time.sleep(1) # loading
        # height after scrolling
        after_h = driver.execute_script("return window.scrollY")
        
        if before_h == after_h:
            break
        before_h = after_h

    try:    
        # Locate the row with '종업원 급여'
        row_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tr[td/span[normalize-space(text())='종업원 급여비용']]"))
        )
        
        # Extract all `span` elements within the row
        span_elements = row_element.find_elements(By.CSS_SELECTOR, "td span")
        row_data = [tab_name]+[span.text.strip() for span in span_elements if span.text.strip()]
        print(f"✅ 종업원 급여 추출된 데이터: {row_data}")
        return row_data
    
    except Exception as e:
        print(f"포괄손익 - 종업원 급여 검색 실패")
        return [tab_name, '종업원 급여비용', '0', '0', '0', '0', '0']

def profit(driver, tab_name):
    time.sleep(1)
    # scroll
    before_h = driver.execute_script("return window.scrollY")
    while True:
        # to the bottom
        driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END) 
        time.sleep(1) # loading
        # height after scrolling
        after_h = driver.execute_script("return window.scrollY")
        
        if before_h == after_h:
            break
        before_h = after_h


    try:
        # Locate the row with '직원급여'
        row_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tr[td/span[normalize-space(text())='직원급여']]"))
        )
        
        # Extract all `span` elements within the row
        span_elements = row_element.find_elements(By.CSS_SELECTOR, "td span")
        row_data = [tab_name] + [span.text.strip() for span in span_elements if span.text.strip()]
        print(f"✅ 직원 급여 추출된 데이터: {row_data}")
        return row_data

    
    except Exception as e:
        print(f"손익계산서 - 직원급여 검색 실패")
        return [tab_name, '직원급여', '0', '0', '0', '0', '0']

def manufactoring(driver, tab_name):
    time.sleep(1)
    before_h = driver.execute_script("return window.scrollY")
    while True:
        # to the bottom
        driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.END) 
        time.sleep(1) # loading
        after_h = driver.execute_script("return window.scrollY")
        if before_h == after_h:
            break
        before_h = after_h


    try:
        # Locate the row with '급여'
        row_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tr[td/span[normalize-space(text())='급여']]"))
        )
        
        # Extract all `span` elements within the row
        span_elements = row_element.find_elements(By.CSS_SELECTOR, "td span")
        row_data = [tab_name]+[span.text.strip() for span in span_elements if span.text.strip()]
        print(f"✅ 급여 추출된 데이터: {row_data}")
        return row_data
    
    except Exception as e:
        print(f"제조 원가 명세서 - 급여 검색 실패")
        return [tab_name, '급여', '0', '0', '0', '0', '0']

# initialize df
total_headers = ['tab', '계정명', '2018-12-31', '2019-12-31', '2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31']
total_df = pd.DataFrame(columns=total_headers)
total_df1 = pd.DataFrame() #2019-2023
total_df2 = pd.DataFrame() #2018-2022


def combine_df(total_df1, total_df2):
    # Merge the two DataFrames on '계정명' and '항목'
    total_df = total_df2.combine_first(total_df1)
    total_df = total_df[total_headers]
    return total_df


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
            

            #driver 실행
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            total_df1 = pd.DataFrame()
            total_df2 = pd.DataFrame()

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
            global search_text

            if navigate_to_financial_page(driver, search_key):
                print(f"🚀 '{search_key}'의 재무 페이지로 성공적으로 이동했습니다.")
                time.sleep(1)

                strong_element = driver.find_element(By.XPATH, '//*[@id="etfi110m1"]/div/div[2]/div/div/div/div[2]/div/strong')
                search_text = strong_element.text.strip()
                print(search_text)
            else:
                print(f"❌ '{search_key}'의 재무 페이지로 이동 실패.")
                

            # 재무 페이지 내부
            # 키워드 집합
            target_tabs = {"재무상태표", "포괄손익계산서", "손익계산서", "제조원가명세서"}


            if change_range(driver, dropdown_id="range", range_value="5"):
                print("범위 변경이 성공적으로 완료되었습니다!")
                time.sleep(1)
            else:
                print("범위 변경에 실패했습니다.")


            # 3 {"재무상태표", "포괄손익계산서", "손익계산서", "제조원가명세서"} 있는지 확인
            try:
                # 탭 그룹에서 모든 탭 가져오기
                tabs = driver.find_elements(By.CSS_SELECTOR, "ul.tab-group-ul > li > a")
                # 📌 존재하는 탭 이름 리스트화
                existing_tabs = {tab.text.strip() for tab in tabs}  # set()으로 저장하여 중복 제거

                # 📌 없는 탭 확인 후 nodata_df() 처리
                missing_tabs = target_tabs - existing_tabs  # target_tabs에서 존재하는 탭을 빼서 부족한 탭 찾기

                if missing_tabs:
                    print(f"존재하지 않는 탭 발견: {missing_tabs}. nodata 처리합니다.")
                    for tab_name in missing_tabs:
                        total_df1 = nodata_df(total_df1, tab_name, 1)
                        continue

                # 📌 실제 존재하는 탭만 반복 처리
                for tab in tabs:
                    tab_name = tab.text.strip() # 탭의 텍스트 가져오기
                    if tab_name not in target_tabs:
                        continue  # target_tabs에 없는 탭이면 무시

                    print(f"탭 '{tab_name}' 확인 중...")
                    driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.HOME)
                    time.sleep(1)


                    tab_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//ul[@class='tab-group-ul']//a[text()='{tab_name}']"))
                    )
                    tab_element.click()

                    # (1) '재무상태표' 처리
                    if tab_name == "재무상태표":
                        # nodata 확인
                        is_nodata = check_nodata(driver, tab_name)

                        if is_nodata:
                            print("재무상태표 탭에 조회된 자료가 없습니다.")
                            total_df1 = nodata_df(total_df1, tab_name, 1)
                            continue
                        else:
                            # 재무상태표 기계장치 확인 코드
                            headers = extract_table_headers(
                                driver=driver,
                                table_selector="div.finance-statement table")
                            machine_row = find_machine_asset(driver, tab_name)
                            total_df1 = create_df(total_df1, machine_row, headers, tab_name)

                    # (2) 나머지 탭 처리
                    else:
                        try:
                        # nodata 확인
                            is_nodata = check_nodata(driver, tab_name)

                            if is_nodata:
                                print(f"{tab_name} 탭에 조회된 자료가 없습니다.")
                                total_df1 = nodata_df(total_df1, tab_name, 1)
                                continue
                            else:
                                # 테이블 헤더 (날짜)
                                headers = extract_table_headers(
                                    driver, table_selector="div.finance-statement table")

                                if headers:
                                    print("추출된 테이블 헤더:", headers)
                                else:
                                    print("테이블 헤더를 추출하지 못했습니다.")
                                
                                if tab_name == "포괄손익계산서":
                                    compre_row = comprehensive(driver, tab_name)
                                    total_df1 = create_df(total_df1, compre_row, headers, tab_name)
                                if tab_name == "손익계산서":
                                    profit_row = profit(driver, tab_name)
                                    total_df1 = create_df(total_df1, profit_row, headers, tab_name)
                                if tab_name == "제조원가명세서":
                                    manufac_row = manufactoring(driver, tab_name)
                                    total_df1 = create_df(total_df1, manufac_row, headers, tab_name)
                                
                        except Exception as e:
                                print(f"테이블 데이터 추출 실패: {e}")

                        
            except Exception as e:
                print(f"세부 페이지 처리 중 오류 발생: {e}")


            #2018 데이터 받아오기

            try:
                tabs = driver.find_elements(By.CSS_SELECTOR, "ul.tab-group-ul > li > a")
                existing_tabs = {tab.text.strip() for tab in tabs}  
                missing_tabs = target_tabs - existing_tabs  # target_tabs에서 존재하는 탭을 빼서 부족한 탭 찾기

                if missing_tabs:
                    print(f"존재하지 않는 탭 발견: {missing_tabs}")
                    for tab_name in missing_tabs:
                        total_df2 = nodata_df(total_df2, tab_name, 2)

                for tab in tabs:
                    tab_name = tab.text.strip() 
                    if tab_name not in target_tabs:
                        continue  

                    print(f"탭 '{tab_name}' 확인 중...")
                    driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.HOME)
                    time.sleep(1)
                
                    tab_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//ul[@class='tab-group-ul']//a[text()='{tab_name}']"))
                    )
                    tab_element.click()

                    get_2018(driver)
                    time.sleep(1)

                    # (1) '재무상태표' 처리
                    if tab_name == "재무상태표":
                        is_nodata = check_nodata(driver, tab_name)

                        if is_nodata:
                            print("재무상태표 탭에 조회된 자료가 없습니다.")
                            total_df2 = nodata_df(total_df2, tab_name, 2)
                            continue
                        else:
                            headers = extract_table_headers(
                                driver=driver,
                                table_selector="div.finance-statement table")
                            machine_row = find_machine_asset(driver, tab_name)
                            total_df2 = create_df(total_df2, machine_row, headers, tab_name)

                    # (2) 나머지 탭 처리
                    else:
                        try:
                            is_nodata = check_nodata(driver, tab_name)

                            if is_nodata:
                                print(f"{tab_name} 탭에 조회된 자료가 없습니다.")
                                total_df2 = nodata_df(total_df2, tab_name, 2)
                                continue
                            else:
                                headers = extract_table_headers(
                                    driver=driver, table_selector="div.finance-statement table")
                                if tab_name == "포괄손익계산서":
                                    compre_row = comprehensive(driver, tab_name)
                                    total_df2 = create_df(total_df2, compre_row, headers, tab_name)
                                if tab_name == "손익계산서":
                                    profit_row = profit(driver, tab_name)
                                    total_df2 = create_df(total_df2, profit_row, headers, tab_name)
                                if tab_name == "제조원가명세서":
                                    manufac_row = manufactoring(driver, tab_name)
                                    total_df2 = create_df(total_df2, manufac_row, headers, tab_name)
                                
                        except Exception as e:
                                print(f"테이블 데이터 추출 실패: {e}") 

            except Exception as e:
                print(f"세부 페이지 처리 중 오류 발생: {e}")
            

            total_df = combine_df(total_df1, total_df2)
            print("total_df", total_df)

            if not total_df.empty:
                    file_path = os.path.join(UPLOAD_FOLDER, f'{search_text}.xlsx')           
                    total_df.to_excel(file_path, index=False)
                    print(f"{search_text} data saved")
            
    except Exception as e:
        print(f"예외 발생: {e}")

    finally:
        # 드라이버 종료가 확실히 호출되도록 함
        if driver:
            driver.execute_script("document.body.style.zoom='100%'")
            driver.quit()
        session['selenium_running'] = False  # 작업 완료 상태로 설정
       
def get_desktop_path():
    base_dir = os.path.expanduser("~")  # 사용자 홈 디렉토리 경로

    system = platform.system()
    if system == "Windows":
        return os.path.join(base_dir, "Desktop")
    elif system == "Darwin":  # macOS
        return os.path.join(base_dir, "Desktop")
    elif system == "Linux":  # Linux
        return os.path.join(base_dir, "Desktop")
    else:
        raise NotImplementedError("이 운영 체제에서는 지원되지 않습니다.")
    
# 바탕화면에 upload 폴더 경로 설정
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FILE_NAME'] = f'{search_text}.xlsx'  # 자동으로 사용할 파일 이름

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    


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
    years_available = [year - i for i in range(1, 4) if (year - i) in machine_costs]
    prev_3_year_avg = sum(machine_costs[y] for y in years_available) / len(years_available) if years_available else 0

    # 인원 계산
    if pogwal_salary is not None:
        salary_increase = max(0, pogwal_salary[year] - pogwal_salary[prev_year])
    elif sonik_salary is not None or jejo_salary is not None:
        sonik_increase = sonik_salary[year] - sonik_salary[prev_year] if sonik_salary else 0
        jejo_increase = jejo_salary[year] - jejo_salary[prev_year] if jejo_salary else 0
        salary_increase = max(0, sonik_increase + jejo_increase)
    else:
        salary_increase = 0

    salary_adjustment = math.floor(salary_increase / 40000) * num

    # 기계장치 계산
    if year == 2019:
        machine_cost_total = (machine_costs.get(year, 0) - machine_costs.get(prev_year, 0)) * 0.07
    elif year == 2020:
        machine_cost_total = (machine_costs.get(year, 0) - machine_costs.get(prev_year, 0)) * 0.1
    elif year in [2021, 2022]:
        machine_cost_total = (machine_costs.get(year, 0) - machine_costs.get(prev_year, 0)) * 0.1 + (machine_costs.get(year, 0) - prev_3_year_avg) * avg_rate
    else:  # year >= 2023
        prev_year_cost = (machine_costs.get(year, 0) - machine_costs.get(prev_year, 0)) * 0.12
        adjusted_cost = (machine_costs.get(year, 0) - prev_3_year_avg) * avg_rate_after_2023
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

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['FILE_NAME'] = f'{search_text}.xlsx'
    
    filename = os.path.join(app.config['UPLOAD_FOLDER'], app.config['FILE_NAME'])

    if not os.path.exists(filename):
        return f"파일이 존재하지 않습니다: {app.config['FILE_NAME']}", 400

    # 첫 번째 시트를 자동으로 선택
    data = pd.read_excel(filename, sheet_name=0, header=0)

    if 'tab' in data.columns:
        data = data.drop(columns=['tab'])
    
    if '계정명' in data.columns:
        data.set_index('계정명', inplace=True)

    # 데이터 전치 및 숫자로 변환
    data = data.transpose()
    data.fillna(0, inplace=True)

    start_year = 2019
    machine_costs, pogwal_salary, sonik_salary, jejo_salary = {}, {}, {}, {}

    # 기계장치 데이터 처리
    if "기계장치" in data.columns:
        machine_costs = {int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
                         for year, value in data["기계장치"].items() if not pd.isna(value)}

    # 종업원 급여비용 데이터 처리
    if "종업원 급여비용" in data.columns:
        pogwal_salary = {int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
                         for year, value in data["종업원 급여비용"].items() if not pd.isna(value)}

    # 직원급여 데이터 처리
    if "직원급여" in data.columns:
        sonik_salary = {int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
                        for year, value in data["직원급여"].items() if not pd.isna(value)}

    # 급여 데이터 처리
    if "급여" in data.columns:
        jejo_salary = {int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
                       for year, value in data["급여"].items() if not pd.isna(value)}

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

    company_name = os.path.splitext(os.path.basename(filename))[0]
    
    return render_template('result.html', results=results, totals=totals, company_name=company_name, start_year=start_year)


  # 웹 브라우저 자동 실행 함수
def open_browser():
    if os.environ.get('FLASK_ENV') == 'development':
        webbrowser.open("http://127.0.0.1:5000")  # 기본 페이지 자동 오픈

def open_browser2():
    if os.environ.get('FLASK_ENV') == 'development':
        webbrowser.open("http://127.0.0.1:5000/calculate") 


if __name__ == '__main__':
    # 스레드를 사용하여 웹 브라우저 실행 (서버와 동시에 실행)
    threading.Timer(1.25, open_browser).start()  # 서버 실행 후 1.25초 후 실행
    app.run(debug=True, use_reloader=False)
