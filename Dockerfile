FROM python:3.12-slim

WORKDIR /workspace

COPY requirements.txt setup.sh run.sh test.sh fixed_plugin.py tests/ ./

RUN apt-get update && apt-get install -y --no-install-recommends curl bash && \
    rm -rf /var/lib/apt/lists/*

RUN chmod +x setup.sh run.sh test.sh && \
    ./setup.sh

CMD ["./test.sh"]
