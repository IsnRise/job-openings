import requests
from itertools import count
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable



def get_sj_salary_statistics(lang, sj_key):
    sj_salaries = []
    town_id = 4
    headers = {
        "X-Api-App-Id" : sj_key
    }
    for page in count(0):
        sj_payload = {
            'keyword': f'программист {lang}',
            'town': town_id,
            'page': page
        }
        superjob_response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=sj_payload)
        superjob_response.raise_for_status()
        superjob_answer = superjob_response.json()
        vacancies_found = superjob_answer['total']
        for vacancy in superjob_answer['objects']:
            salary_from = vacancy['payment_from']
            salary_to = vacancy['payment_to']
            salary_currency = vacancy['currency']
            sj_salary = predict_rub_salary(salary_from, salary_to, salary_currency)
            if sj_salary:
                sj_salaries.append(sj_salary)
        if not superjob_answer['more']:
            break
    vacancies_processed = len(sj_salaries)
    if vacancies_processed:
        average_salary = sum(sj_salaries) // vacancies_processed
    else:
        average_salary = 0
    return { 
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
        "average_salary": average_salary
    }


def predict_rub_salary(salary_from, salary_to, salary_currency):
    if salary_currency != 'RUR' and salary_currency != 'rub':
        return None
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_to:
        return salary_to * 0.8
    elif salary_from:
        return salary_from * 1.2


def get_hh_salary_statistics(lang):
    hh_salaries = []
    area_id = 1
    for page in count(0):
        payload = {
            'text': f'программист {lang}',
            'area': area_id,
            'page': page
        }
        response_hh = requests.get('https://api.hh.ru/vacancies', params=payload)
        response_hh.raise_for_status()
        response_hh_payload = response_hh.json()
        for vacancy in response_hh_payload['items']:
            vacancy_salary = vacancy['salary']
            if not vacancy_salary:
                continue
            salary_from = vacancy_salary['from']
            salary_to = vacancy_salary['to']
            salary_currency = vacancy_salary['currency']
            salary = predict_rub_salary(salary_from, salary_to, salary_currency)
            if salary:
                hh_salaries.append(salary)
        if page == response_hh_payload['pages'] - 1:
            break
    vacancies_found = response_hh_payload['found']
    vacancies_processed = len(hh_salaries)
    if vacancies_processed:
        average_salary = sum(hh_salaries) // vacancies_processed
    else:
        average_salary = 0
    return { 
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
        "average_salary": average_salary
    }



def make_table(lang_salaries, title):
    table_content = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang, vacancy in lang_salaries.items():
        raw = [lang, vacancy['vacancies_found'], vacancy['vacancies_processed'], vacancy['average_salary']]
        table_content.append(raw)
    table = AsciiTable(table_content, title)
    return table.table


if __name__ == '__main__':
    load_dotenv()
    sj_key = os.getenv('SUPERJOB_KEY')
    prog_langs = [
        'JavaScript',
        'Java',
        'Python'
    ]
    lang_salaries_statistics_hh = {}
    lang_salaries_statistics_sj = {}
    title_sj = 'SuperJob Moscow'
    title_hh = 'HeadHunter Moscow'
    for lang in prog_langs:
        lang_salary_statistics_sj = get_sj_salary_statistics(lang, sj_key)
        lang_salaries_statistics_sj[lang] = lang_salary_statistics_sj
        lang_salary_statistics_hh = get_hh_salary_statistics(lang)
        lang_salaries_statistics_hh[lang] = lang_salary_statistics_hh
    table_sj = make_table(lang_salaries_statistics_sj, title_sj)
    table_hh = make_table(lang_salaries_statistics_hh, title_hh)
    print(table_sj)
    print(table_hh)
