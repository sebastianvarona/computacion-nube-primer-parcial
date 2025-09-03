FROM python:3.9-slim

EXPOSE 5004

WORKDIR /app

COPY ./microOrders/requirements.txt .
RUN pip install -r requirements.txt

# Copy shared utilities first
COPY ./shared /app/shared

COPY ./microOrders .

CMD ["python", "run.py"]