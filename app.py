from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import pandas as pd
import math

app = Flask(__name__)

app.secret_key = os.urandom(24)

# 업로드 폴더 설정
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
        machine_cost_total = (machine_costs.get(year, 0) - machine_costs.get(prev_year, 0)) * 0.12 + (machine_costs.get(year, 0) - prev_3_year_avg) * avg_rate_after_2023

    total = machine_cost_total + salary_adjustment
    return machine_cost_total, salary_adjustment, total


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
             return "파일이 없습니다.", 400
        file = request.files['file']
        if file.filename == '':
            return "파일이 선택되지 않았습니다.", 400
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            
            file.save(filename)
            session['uploaded_file'] = filename

            # 엑셀 파일을 읽어 데이터 로드
            try:
                data = pd.read_excel(filename, None)  # Read all sheets into a dictionary
                sheet_names = data.keys()  # Get the sheet names
                return render_template('company_select.html', sheet_names=sheet_names)
            except Exception as e:
                return f"엑셀 파일을 읽는 중 오류 발생: {e}" ,500

    return render_template('upload.html')

#문자열 숫자변환

def convert_to_numeric(value):
    if isinstance(value, str):
        return float(value.replace(',', '').strip())
    return value


@app.route('/calculate', methods=['POST'])
def calculate():
    start_year = int(request.form['start_year'])
    company_name = request.form['company_name']
    
    filename = session.get('uploaded_file')
    if not filename:
        return redirect(url_for('upload_file'))
    
    data = pd.read_excel(filename, sheet_name=company_name)
    data = data.drop(columns=data.columns[0])
    data = data.set_index(data.columns[0])
    data = data.transpose()

    machine_costs = {}
    pogwal_salary = {}
    sonik_salary = {}
    jejo_salary = {}

    #로그확인
    #print(data.head())  # 데이터 확인
    #print(data.columns)  # 컬럼 확인

    # 기계장치 데이터 처리
    if "기계장치" in data.columns:
        machine_costs = {
            int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
            for year, value in data["기계장치"].items() if not pd.isna(value)
        }
    else:
        machine_costs = {}

    # 종업원 급여비용 데이터 처리
    if "종업원 급여비용" in data.columns:
        pogwal_salary = {
            int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
            for year, value in data["종업원 급여비용"].items() if not pd.isna(value)
        }
    else:
        pogwal_salary = {}

    # 직원급여 데이터 처리
    if "직원급여" in data.columns:
        sonik_salary = {
            int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
            for year, value in data["직원급여"].items() if not pd.isna(value)
        }
    else:
        sonik_salary = {}

    # 급여 데이터 처리
    if "급여" in data.columns:
        jejo_salary = {
            int(year.split('-')[0]) if isinstance(year, str) else year.year: convert_to_numeric(value)
            for year, value in data["급여"].items() if not pd.isna(value)
        }
    else:
        jejo_salary = {}

    #로그 확인
    #print("Machine Costs:", machine_costs)
    #print("Pogwal Salary:", pogwal_salary)
    #print("Sonik Salary:", sonik_salary)
    #print("Jejo Salary:", jejo_salary)

    if not pogwal_salary and not sonik_salary and not jejo_salary:
        return "포괄 급여나 손익/제조 급여가 필요합니다.", 400
    elif not pogwal_salary:
        pogwal_salary = None  # 명시적으로 설정

    results = {}
    total_machine_cost = 0
    total_salary_adjustment = 0
    total_cost = 0

    # 연도별 비용 계산
    for year in range(start_year, start_year + 5):
        try:
            machine_cost_total, salary_adjustment, total = calculate_yearly_cost(
                year,
                machine_costs=machine_costs,
                pogwal_salary=pogwal_salary,
                sonik_salary=sonik_salary,
                jejo_salary=jejo_salary
            )
            results[year] = {
                "machine_cost_total": round(machine_cost_total),
                "salary_adjustment": round(salary_adjustment),
                "total": round(total),
            }

            # 총합 계산 (시작년도부터 5개년치)
            total_machine_cost += machine_cost_total
            total_salary_adjustment += salary_adjustment
            total_cost += total

        except KeyError as e:
            results[year] = {"error": f"데이터가 없습니다: {e}"}
        except ValueError as e:
            results[year] = {"error": f"계산 오류: {e}"}

    # 총합 결과를 추가
    totals = {
        "machine_cost_total": round(total_machine_cost),
        "salary_adjustment": round(total_salary_adjustment),
        "total": round(total_cost),
    }

    return render_template('result.html', results=results, totals=totals, company_name=company_name, start_year=start_year)


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)  # 업로드 폴더가 없으면 생성
    app.run(debug=True)
