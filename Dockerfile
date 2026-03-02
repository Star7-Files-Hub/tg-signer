FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir ".[gui]"

EXPOSE 7001

VOLUME [ "/app/.signer" ]

CMD ["tg-signer", "web"]