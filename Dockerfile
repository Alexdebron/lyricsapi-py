FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 1200

ENV PORT=1200

CMD ["gunicorn", "--bind", "0.0.0.0:1200", "app:app"]
