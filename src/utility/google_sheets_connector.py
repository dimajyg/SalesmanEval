import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from src.config import SHEETS_TOKEN, SHOPS

def get_salesman_data(gsheet_name):
    """
    Retrieves salesman data from the 'Продавцы' sheet.

    Returns:
        dict: A dictionary where keys are dates (datetime objects) and values are dictionaries 
              mapping shop names to salesman names.  Returns an empty dictionary if there's an error.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(SHEETS_TOKEN, scope)
        client = gspread.authorize(creds)
        sheet = client.open(gsheet_name).worksheet("Продавцы")  

        # Get header row to find column indices
        header = sheet.row_values(1)
        date_index = header.index("Дата")
        shop_indices = {shop: header.index(shop) for shop in SHOPS if shop in header}
        data = {}
        for row in sheet.get_all_values()[1:]: # Skip header row
            try:
                date_str = row[date_index]
                date = datetime.strptime(date_str, "%d.%m.%Y").date() # Adjust format if needed

                shop_data = {}
                for shop, index in shop_indices.items():
                    if row[index]:
                        shop_data[shop] = row[index]
                if shop_data:
                    data[date] = shop_data
            except (ValueError, IndexError):
                print(f"Skipping invalid row: {row}")
                continue

        return data
    except Exception as e:
        print(f"Error retrieving salesman data: {e}")
        return {}


def ensure_shop_columns(gsheet_name):
    """Ensures that each shop in SHOPS has a column in the 'Продавцы' sheet."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SHEETS_TOKEN, scope)
    client = gspread.authorize(creds)
    sheet = client.open(gsheet_name).worksheet("Продавцы")

    existing_columns = sheet.row_values(1)
    for shop in SHOPS:
        if shop not in existing_columns:
            sheet.insert_col(len(existing_columns)+1, values = [[shop]])



def store_metrics(metrics_list, gsheet_name):
    """Stores metrics data in the 'Метрики' sheet."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SHEETS_TOKEN, scope)
    client = gspread.authorize(creds)
    sheet = client.open(gsheet_name).worksheet("Метрики")

    #Get header row to find column indices. If sheet is empty, create header row.
    header = sheet.row_values(1)
    if not header:
        header = list(metrics_list[0].keys())
        sheet.append_row(header)

    for m in metrics_list:
        row_data = [str(m.get(key, "")) for key in header]
        sheet.append_row(row_data)
