import requests
import csv
import os
from datetime import datetime, timedelta
import pandas as pd

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

        # Вставляем отладочный вывод для проверки данных
        print(leads_data)  # Выводит полный ответ JSON

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

    file_path = 'facebook_ads_leads_data.csv'  # Имя итогового файла

    if all_leads:
        print(f"Запись {len(all_leads)} записей в файл")
        # Используем pandas для записи в CSV и отображения таблицы
        df = pd.DataFrame(all_leads)
        df.to_csv(file_path, index=False)

        # Отобразим итоговые данные в виде таблицы
        print("\nИтоговые данные в виде таблицы:\n")
        print(df)
    else:
        print("Нет данных для экспорта")

    # Добавляем метку времени в конец файла, чтобы GitHub видел изменения
    with open(file_path, 'a') as f:
        updated_time = datetime.now().isoformat()
        f.write(f"\n# Last updated: {updated_time}\n")
        print(f"Метка времени обновлена: {updated_time}")

    print("Данные успешно экспортированы в", file_path)

if __name__ == "__main__":
    fetch_leads_data()
