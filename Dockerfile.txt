# Usa Python 3.10 como base
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Comando para iniciar o Streamlit
CMD streamlit run dashboard_clima_lavras.py --server.port $PORT --server.headless true
