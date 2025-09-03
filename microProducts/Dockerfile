FROM python:3.9-slim

EXPOSE 5003

WORKDIR /app

COPY ./microProducts/requirements.txt .
RUN pip install -r requirements.txt

# Copy shared utilities first
COPY ./shared /app/shared

COPY ./microProducts .

CMD ["python", "run.py"]