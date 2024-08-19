import os
import json
import gspread
import requests
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pandas as pd

def fetch_leads_data():
    # SCOPES для работы с Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Получаем учетные данные из переменной среды
    credentials = Credentials.from_service_account_info(
        json.loads(os.environ['GOOGLE_CREDENTIALS']),
        scopes=SCOPES
    )

    # Авторизация в Google Sheets API
    client = gspread.authorize(credentials)

    # Открываем Google Таблицу
    sheet = client.open("Название_таблицы").sheet1

    access_token = os.getenv('ACCESS_TOKEN')
    ad_account_id = os.getenv('AD_ACCOUNT_ID')

    if not access_token or not ad_account_id:
        print("ACCESS_TOKEN или AD_ACCOUNT_ID не установлены")
        return

    # Даты
    end_date = datetime.now() - timedelta(days=1)
    end_date_str = end_date.strftime('%Y-%m-%d')
    start_date = '2024-06-01'  # Начальная дата

    # Получаем список объявлений
    url = f'https://graph.facebook.com/v20.0/act_{ad_account_id}/ads'
    params = {
        'access_token': access_token,
        'fields': 'id,name'
    }

    response = requests.get(url, params=params)
    ads = response.json()

    if 'error' in ads:
        print(f"Ошибка в ответе API: {ads['error']}")
        return

    if 'data' not in ads:
        print("Ответ API не содержит ключ 'data'")
        return

    all_leads = []

    for ad in ads['data']:
        ad_id = ad['id']
        ad_name = ad['name']

        # Получаем данные по лидам для каждого объявления
        lead_url = f'https://graph.facebook.com/v20.0/{ad_id}/leads'
        lead_params = {
            'access_token': access_token,
            'fields': 'id,created_time,ad_id,ad_name,campaign_id,campaign_name,form_name,platform,full_name,phone_number'
        }

        leads_response = requests.get(lead_url, params=lead_params)
        leads_data = leads_response.json()

        print(leads_response.json())  # Выводит полный ответ JSON

        if 'error' in leads_data:
            print(f"Ошибка в ответе API при запросе лидов: {leads_data['error']}")
            continue

        if 'data' not in leads_data:
            print(f"Ответ API не содержит ключ 'data' для объявления {ad_name}")
            continue

        print(f"Объявление: {ad_name}, Количество лидов: {len(leads_data['data'])}")

        for lead in leads_data['data']:
            # Проверка, попадает ли лид в нужный диапазон дат
            lead_date = lead['created_time'][:10]
            if start_date <= lead_date <= end_date_str:
                all_leads.append({
                    'ID': lead['id'],
                    'Время создания': lead['created_time'],
                    'ID рекламы': lead['ad_id'],
                    'Название рекламы': lead['ad_name'],
                    'ID кампании': lead['campaign_id'],
                    'Название кампании': lead['campaign_name'],
                    'Название формы': lead.get('form_name', 'Unknown'),
                    'Платформа': lead.get('platform', 'Unknown'),
                    'Полное имя': lead.get('full_name', 'No name available'),
                    'Номер телефона': lead.get('phone_number', 'No phone available')
                })

    if all_leads:
        print(f"Запись {len(all_leads)} записей в Google Таблицу")
        # Преобразуем данные в DataFrame для записи
        df = pd.DataFrame(all_leads)

        # Очистим Google Таблицу перед записью
        sheet.clear()

        # Запишем данные в Google Таблицу
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

        # Отобразим итоговые данные в виде таблицы
        print("\nИтоговые данные в виде таблицы:\n")
        print(df)
    else:
        print("Нет данных для экспорта")

    print("Данные успешно экспортированы в Google Таблицу")

if __name__ == "__main__":
    fetch_leads_data()
