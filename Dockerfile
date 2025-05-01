FROM python:3.12-slim
WORKDIR /app
COPY . /app/
RUN apt-get update && apt-get install -y gcc libffi-dev python3-dev && apt-get clean
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "events_app.wsgi:application"]

