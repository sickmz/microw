## Overview
This is a telegram bot that interacts with Google Sheets and allows you to add, delete, make an expense list and show various graphs.

## What's new?
- 📝 **Local `.xlsx` file management**: now by default all saved, deleted expenses, charts and lists are produced locally, under your control.
- 🌐 **Sync with Google Sheet**: you can synchronize the last expenses you entered in your local `.xlsx` directly to Google Sheets.
    - **Automatic sync**: a background task wakes up every few minutes (configurable) and sync new expenses (if there are any new ones) with your Google Sheets. You can enable or disable Google Sheets synchronization via the `⚙️ Settings` command.
- All operations are now ***extremely faster*** because of the work being done locally. Google's API is very slow, so a batch synchronization of expenses is the best solution to ensure maximum responsiveness.
- To improve readability and maintenance, the code was split into modules.

**Next step?**
- [x] ~~Initial decision screen between Google Sheets and *save data locally* in .csv format with ability to export and share (for those not planning to use gsheet).~~
- [x] ~~Improve the speed of execution for the elimination of an expense~~
- [x] ~~Simplify the code and make it more modular~~
- [ ] Creation of budgets with alerts if exceeded.
- [ ] Income management
- [ ] Cash account
- [ ] Investments

## Feature
- `✏️ Add` expense with two dependent lists, category and subcategory.
- `❌ Delete` expense with pagination to go back through older expenses.
- `📊 Charts` of four types: yearly and monthly breakdowns, trends, and heatmaps.
- `📋 List` to displays a summary of expenses for the current year.
- `🔄 Reset` the conversation with the bot.
- `⚙️ Settings` show the system settings (currently Google Sheet sync)

## Demo

<div align="center">
  <video src="https://github.com/sickmz/microw/assets/24682196/59692629-47bc-46b0-a5d0-fbc904215262" width="400" />
</div>

## Installation

1. Clone the repository:

```
git clone https://github.com/sickmz/microw.git
cd microw
```

## Create a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

## Install the required packages:

```
pip install -r requirements.txt
```

## Create a Google Service Account
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project or select an existing one.
- Enable the Google Sheet Api for this project.
- Navigate to the "APIs & Services" > "Credentials" section.
- Click "Create credentials" > "Service account".
- Fill in the service account details and click "Create".
- Click "Furnish a new private key" > "JSON" > "Create". The JSON file will be downloaded automatically.
- Rename the downloaded file to credentials.json and place it in the root directory of the project.
- Share your spreadsheet with the email of Google Service Account.

## `.env` configuration

1. Create a `.env` file in the root directory of the project:

```
touch .env
```

2. Open the `.env` file in a text editor and add the following lines, replacing the placeholders with your actual values:

```
SPREADSHEET_ID=your_remote_spreadsheet_id
BOT_TOKEN=your_telegram_bot_token
EXPENSE_SHEET=your_remote_expense_sheet_name
LOCAL_EXPENSE_PATH=your-local-expense-sheet (example: 'spreadsheet/expenses.xlsx')
USER_ID=your_telegram_user_id
```

3. Make sure to add `.env` to your `.gitignore` file to prevent accidental commits.

## (Optional) Setting as Systemd Service:

1. Create a new systemd service file:

```
sudo nano /etc/systemd/system/microw.service
```

2. Copy the following content into the file:

```
[Unit]
Description=microw
After=network.target

[Service]
Type=simple
ExecStart=/home/$USER/code-server/workspace/microw/venv/bin/python3 main.py
WorkingDirectory=/home/$USER/code-server/workspace/microw

[Install]
WantedBy=multi-user.target
```

3. Replace the ExecStart and WorkingDirectory paths with the actual paths to your script and project directory.

4. Reload the systemd daemon, enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl enable microw.service
sudo systemctl start microw.service
```

4. Check the service status:

```
sudo systemctl status microw.service
```

## Usage

1. Start a conversation with the bot on Telegram.
2. Use the `/start` command to initiate interaction.
3. Choose an action from the provided options: `✏️ Add`, `❌ Delete`, `📊 Charts`, `📋 List` or `⚙️ Settings`.
4. Follow the bot's prompts.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
