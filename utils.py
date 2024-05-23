import os
import json
from openpyxl import load_workbook, Workbook
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import gspread
from config import LOCAL_EXPENSE_PATH


def build_keyboard(options: list) -> InlineKeyboardMarkup:
    """
    Build an inline keyboard.
    Each option becomes a button with the same label and callback data.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(option, callback_data=option)]
        for option in options
    ])


def is_expense_file_empty():
    """
    Check if the local expense file is empty or contains only the header row.
    """
    wb, ws = get_workbook_and_sheet(LOCAL_EXPENSE_PATH)
    return ws.max_row <= 1


def ensure_spreadsheet_path(file_path):
    """
    Ensure the directory for the spreadsheet exists and create the file with a header if it doesn't exist.
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    if not os.path.exists(file_path):
        wb = Workbook()
        ws = wb.active
        ws.append(["Month", "Category", "Subcategory",
                  "Price", "Date", "Timestamp"])
        wb.save(file_path)


def get_workbook_and_sheet(file_path):
    """
    Load the workbook and active sheet, ensuring the file and path exist.
    """
    ensure_spreadsheet_path(file_path)
    wb = load_workbook(file_path)
    ws = wb.active
    return wb, ws


def load_settings():
    """
    Load settings from a JSON file. If the file doesn't exist, create it with default settings.
    """
    if not os.path.exists('settings.json'):
        settings = {'google_sync_enabled': False, 'last_upload': None}
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    else:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
    return settings


def save_settings(settings):
    """
    Save the given settings to a JSON file.
    """
    with open('settings.json', 'w') as f:
        json.dump(settings, f)


def get_worksheet(spreadsheet_id, worksheet_name):
    """
    Get the specified worksheet from a Google Sheets spreadsheet using its ID and worksheet name.
    Requires credentials stored in 'credentials.json'.
    """
    gc = gspread.service_account(filename='credentials.json')
    return gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)


def ensure_charts_path():
    """
    Ensure the directory for storing charts exists, creating it if necessary.
    """
    if not os.path.exists('charts'):
        os.makedirs('charts')
