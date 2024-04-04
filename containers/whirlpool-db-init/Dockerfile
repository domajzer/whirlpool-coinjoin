FROM python:3.9-slim
WORKDIR /usr/src/app
RUN pip install pymysql cryptography
COPY db.py .

RUN useradd --uid 1001 --create-home --shell /bin/bash --no-log-init appuser
RUN chown -R appuser:appuser /usr/src/app
USER 1001

ENTRYPOINT ["python", "./db.py"]
