FROM python:3.11-slim

WORKDIR /app

# Instala dependências críticas de sistema para compilar o driver do PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copia e instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código para dentro do contêiner
COPY . .

# Comando padrão ao iniciar o contêiner
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]