FROM python:3.7

WORKDIR /usr/share/test_app

COPY . .

RUN python -m pip install -r requirements.txt

CMD ["python", "main.py"]