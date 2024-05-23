import os
import json
from openpyxl import load_workbook, Workbook
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import gspread
from config import LOCAL_EXPENSE_PATH


def build_keyboard(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(option, callback_data=option)]
        for option in options
    ])


def is_expense_file_empty():
    wb, ws = get_workbook_and_sheet(LOCAL_EXPENSE_PATH)
    return ws.max_row <= 1


def ensure_spreadsheet_path(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    if not os.path.exists(file_path):
        wb = Workbook()
        ws = wb.active
        ws.append(["Month", "Category", "Subcategory",
                  "Price", "Date", "Timestamp"])
        wb.save(file_path)


def get_workbook_and_sheet(file_path):
    ensure_spreadsheet_path(file_path)
    wb = load_workbook(file_path)
    ws = wb.active
    return wb, ws


def load_settings():
    if not os.path.exists('settings.json'):
        settings = {'google_sync_enabled': False, 'last_upload': None}
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    else:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
    return settings


def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)


def get_worksheet(spreadsheet_id, worksheet_name):
    gc = gspread.service_account(filename='credentials.json')
    return gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)


def ensure_charts_path():
    if not os.path.exists('charts'):
        os.makedirs('charts')
