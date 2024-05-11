## Overview
This is a telegram bot that interacts with Google Sheets to save expenses based on user input.

## Demo
![demo](https://github.com/sickmz/microw/assets/24682196/adb826ae-2834-484e-a2de-e93dc21f191c)

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
SPREADSHEET_ID=your_spreadsheet_id
BOT_TOKEN=your_bot_token
EXPENSE_SHEET=your_expense_sheet_name
USER_ID=your_user_id
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
ExecStart=/home/$USER/code-server/workspace/microw/venv/bin/python3 microw.py
WorkingDirectory=/home/$USER/code-server/workspace/microw

[Install]
WantedBy=multi-user.target
```

3. Replace the ExecStart and WorkingDirectory paths with the actual paths to your script and project directory.

4. Reload the systemd daemon:

```
sudo systemctl daemon-reload
```

5. Enable the service:

```
sudo systemctl enable microw.service
```

6. Start the service:

```
sudo systemctl start microw.service
```

7. Check the service status:

```
sudo systemctl status microw.service
```

## Usage

1. Start a conversation with the bot on Telegram.
2. Use the /start command to begin tracking an expense.
3. Follow the bot's prompts to select a category, subcategory, and enter the price.
4. If you wish to cancel the process at any point, use the /cancel command.
5. The expense will be recorded in the Google Spreadsheet upon successful entry.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
