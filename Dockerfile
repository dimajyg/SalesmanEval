# Базовый образ Python
FROM python:3.9-slim

# Установка рабочей директории в контейнере
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта
COPY . .

# Команда для запуска приложения
CMD ["python", "src/main.py"]