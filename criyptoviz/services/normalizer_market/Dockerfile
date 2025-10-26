FROM python:3.11-slim
WORKDIR /app
RUN pip install kafka-python==2.0.2 psycopg2-binary==2.9.9 pydantic==2.8.2
COPY common /app/common
COPY services/normalizer_market/main.py /app/main.py
CMD ["python","/app/main.py"]
