FROM python:3.10-slim

WORKDIR /usr/src/app

COPY src/ /usr/src/app/src
COPY requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/usr/src/app/src/main.py"]
