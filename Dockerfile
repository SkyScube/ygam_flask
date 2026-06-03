FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV FLASK_CREATE_TABLES=true

CMD ["python", "-c", "from src import create_app; from src.extensions import socketio; app = create_app(create_tables=True); socketio.run(app, host='0.0.0.0', port=5000)"]
