FROM python:3.11-slim
WORKDIR /app
RUN pip install websockets==12.0 kafka-python==2.0.2 pydantic==2.8.2
COPY common /app/common
COPY services/scraper_coinbase/main.py /app/main.py
CMD ["python","/app/main.py"]
