FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Evitar buffering de salida de Python
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . .

# Exponer el puerto por defecto de Streamlit
EXPOSE 8501

# El comando por defecto se sobreescribirá en docker-compose
CMD ["streamlit", "run", "tienda_cliente.py"]
