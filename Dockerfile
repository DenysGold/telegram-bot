# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем переменную окружения для Flask
ENV FLASK_APP=main.py

# Открываем порт для Cloud Run
EXPOSE 8080

# Запускаем бота и Flask сервер через Python
CMD ["python3", "main.py"]
