import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
import gspread

# Настройка авторизации для Google Sheets через секрет GOOGLE_CREDENTIALS
credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
creds = service_account.Credentials.from_service_account_info(credentials_info)
client = gspread.authorize(creds)

# Открываем Google Таблицу по названию
sheet = client.open("KO_Лиды").sheet1

def fetch_leads_data():
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

        if 'error' in leads_data:
            print(f"Ошибка в ответе API при запросе лидов: {leads_data['error']}")
            continue

        if 'data' not in leads_data:
            print(f"Ответ API не содержит ключ 'data' для объявления {ad_name}")
            continue

        for lead in leads_data['data']:
            # Проверка, попадает ли лид в нужный диапазон дат
            lead_date = lead['created_time'][:10]
            if start_date <= lead_date <= end_date_str:
                # Добавляем данные лида в Google Таблицу
                sheet.append_row([
                    lead['id'], 
                    lead['created_time'], 
                    lead['ad_id'], 
                    lead['ad_name'], 
                    lead['campaign_id'], 
                    lead['campaign_name'], 
                    lead.get('form_name', 'Unknown'), 
                    lead.get('platform', 'Unknown'), 
                    lead.get('full_name', 'No name available'), 
                    lead.get('phone_number', 'No phone available')
                ])

    print("Данные успешно экспортированы в Google Таблицу")

if __name__ == "__main__":
    fetch_leads_data()
