from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from utils import get_workbook_and_sheet, get_worksheet, save_settings, load_settings
from config import logger

from config import SPREADSHEET_ID, EXPENSE_SHEET

from constants import EXPENSE_PATH 


def sync_to_google_sheets():
    """
    Sync local expenses data to Google Sheets if synchronization is enabled.
    Only uploads new records since the last upload timestamp.
    """
    logger.info("Sync function started")
    settings = load_settings()
    if settings['google_sync']['enabled']:
        logger.info("Google sync is enabled")
        wb, ws = get_workbook_and_sheet(EXPENSE_PATH)
        df = pd.DataFrame(ws.values)
        if len(df.columns) > 0:
            df.columns = df.iloc[0]
            df = df[1:]

        last_upload = pd.to_datetime(settings.get('last_upload'))
        new_records = df[pd.to_datetime(
            df['Timestamp']) > last_upload] if last_upload else df

        if not new_records.empty:
            logger.info(f"New records to upload: {len(new_records)}")
            sheet = get_worksheet(SPREADSHEET_ID, EXPENSE_SHEET)
            records_to_upload = new_records[
                ['Month', 'Category', 'Subcategory', 'Price', 'Date']
            ].values.tolist()
            for record in records_to_upload:
                sheet.append_row(record)
                logger.info(f"Uploaded record: {record}")

            new_last_upload = pd.to_datetime(new_records['Timestamp']).max()
            settings['last_upload'] = new_last_upload.isoformat()
            save_settings(settings)
        else:
            logger.info("No new records to upload")
    else:
        logger.info("Google sync is disabled")

def start_scheduler():
    """
    Start the background scheduler to run the sync function at regular intervals.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_to_google_sheets, 'interval', minutes=30)
    scheduler.start()
    return scheduler
