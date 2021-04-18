FROM python:3.8.6

WORKDIR /usr/share/test_app

COPY . .

RUN python -m pip install -r requirements.txt

CMD ["python", "main.py"]
