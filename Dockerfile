FROM python:3.10.5

RUN pip install --upgrade pip
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./model /code/model

CMD ["uvicorn", "model.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
