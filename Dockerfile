FROM python:3.8

WORKDIR /usr/share/test_app

COPY . .

RUN git clone https://github.com/maraid/fbchat.git fbchat
RUN cd fbchat
RUN python -m pip install .
RUN cd -

RUN python -m pip install -r requirements.txt

CMD ["python", "main.py"]