FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./

EXPOSE 6969

ENV JISHAKU_NO_DM_TRACEBACK=true

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "./core.py" ]
