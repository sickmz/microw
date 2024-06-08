import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from config import REMOTE_EXPENSE_SHEET, REMOTE_SPREADSHEET_ID, logger
from utils import (
    get_local_expense_wb,
    get_remote_expense_wb,
    load_settings,
    save_settings,
)


def sync_to_google_sheets():
    """
    Sync local expenses data to Google Sheets if synchronization is enabled.
    Only uploads new records since the last upload timestamp.
    """
    logger.info("Sync function started")
    settings = load_settings()
    if settings["google_sync"]["enabled"]:
        logger.info("Google sync is enabled")
        wb, ws = get_local_expense_wb()
        df = pd.DataFrame(ws.values)
        if len(df.columns) > 0:
            df.columns = df.iloc[0]
            df = df[1:]

        last_upload = pd.to_datetime(settings["google_sync"].get("last_upload"))
        new_records = (
            df[pd.to_datetime(df["Timestamp"]) > last_upload] if last_upload else df
        )

        if not new_records.empty:
            logger.info(f"New records to upload: {len(new_records)}")
            sheet = get_remote_expense_wb(REMOTE_SPREADSHEET_ID, REMOTE_EXPENSE_SHEET)
            records_to_upload = new_records[
                ["Month", "Category", "Subcategory", "Price", "Date"]
            ].values.tolist()
            for record in records_to_upload:
                sheet.append_row(record)
                logger.info(f"Uploaded record: {record}")

            new_last_upload = pd.to_datetime(new_records["Timestamp"]).max()
            settings["google_sync"]["last_upload"] = new_last_upload.isoformat()
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
    scheduler.add_job(sync_to_google_sheets, "interval", minutes=5)
    scheduler.start()
    return scheduler
