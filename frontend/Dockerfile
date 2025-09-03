FROM python:3.9-slim

EXPOSE 5001

WORKDIR /app

COPY ./frontend/requirements.txt .
RUN pip install -r requirements.txt

# Copy shared utilities first
COPY ./shared /app/shared

COPY ./frontend .

CMD ["python", "run.py"]