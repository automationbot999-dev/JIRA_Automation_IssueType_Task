FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /myapp

COPY . .

RUN pip install --upgrade pip && \
    pip install \
        playwright \
        playwright==1.55.0 \
        robotframework \
        robotframework-requests \
        robotframework-restlibrary \
        python-dotenv \
        jsonpath-ng \
        jsonschema

ENV ENV_FILE_PATH=/app/Library/.env

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
