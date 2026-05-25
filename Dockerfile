FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные библиотеки, необходимые для работы Pillow (сжатие картинок, шрифты)
RUN apt-get update && apt-get install -y \
    fontconfig \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .

# Команда для запуска бота
CMD ["python", "main.py"]
