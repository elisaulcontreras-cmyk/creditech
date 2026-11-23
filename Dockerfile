FROM python:3.13-slim

WORKDIR /app

# Instalar solo las dependencias del servidor web y generador de Excel (sin PyQt6 que es para las laptops)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn>=0.32.0" \
    "sqlalchemy>=2.0.0" \
    "httpx>=0.27.0" \
    "xlsxwriter>=3.2.0" \
    "psycopg2-binary>=2.9.9"

COPY shared ./shared
COPY server ./server
COPY run_server.py ./run_server.py

ENV CREDITECH_HOST=0.0.0.0
ENV CREDITECH_PORT=8085

EXPOSE 8085

CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8085}"]
