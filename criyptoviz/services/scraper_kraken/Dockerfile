FROM python:3.11-slim
WORKDIR /app
# Certificats SSL pour WSS
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN pip install websockets==12.0 kafka-python==2.0.2 pydantic==2.8.2
COPY common /app/common
COPY services/scraper_kraken/main.py /app/main.py
CMD ["python","-u","/app/main.py"]
