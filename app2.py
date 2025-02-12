from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import math
from finance_page import login_to_site, navigate_to_financial_page, search_text
import threading
import webbrowser

app = Flask(__name__)

app.secret_key = os.urandom(24)


# 업로드 폴더 설정
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FILE_NAME'] = f'{search_text}.xlsx'  # 자동으로 사용할 파일 이름

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         # 사용자가 입력한 로그인 정보 가져오기
#         username = request.form['username'].strip()
#         password = request.form['password'].strip()
#         search_key = request.form['search_key'].strip()

#         # 로그인 정보 검증 (예제에서는 간단한 검증, 실제 사용 시 DB 활용 가능)
#         if username and password and search_key:
#             # 세션에 저장하여 다른 페이지에서 사용 가능하도록 함
#             session['username'] = username
#             session['password'] = password
#             session['search_key'] = search_key

#             return redirect(url_for('calculate'))  # 로그인 성공 시 계산 페이지로 이동
#         else:
#             return render_template('login.html', error="모든 정보를 입력하세요.")

#     return render_template('login.html')

# @app.route('/', methods=['GET'])
# def index():
#     return redirect(url_for('login'))

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


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('calculate'))


def convert_to_numeric(value):
    """문자열을 숫자로 변환하고, '-' 같은 특수문자는 NaN으로 처리"""
    if isinstance(value, str):
        if value.strip() == '-' or value.strip() == '':
            return float('nan')
        return float(value.replace(',', '').strip())
    return value


@app.route('/calculate', methods=['GET'])
def calculate():
    # if 'username' not in session:
    #     return redirect(url_for('login'))  # 로그인하지 않았으면 로그인 페이지로

    # username = session['username']
    # password = session['password']
    # search_key = session['search_key']

    # # finance_page.py 실행 (입력값 전달)
    # navigate_to_financial_page(search_key)
    # login_to_site(username, password)

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
    webbrowser.open("http://127.0.0.1:5000")  # 기본 페이지 자동 오픈

if __name__ == '__main__':
    # 스레드를 사용하여 웹 브라우저 실행 (서버와 동시에 실행)
    threading.Timer(1.25, open_browser).start()  # 서버 실행 후 1.25초 후 실행
    app.run(debug=True, use_reloader=False)