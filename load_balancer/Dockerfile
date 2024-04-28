FROM python:3.8-slim

WORKDIR /load_balancer

COPY . /load_balancer

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

#CMD ["python", "balancer.py"]
CMD gunicorn --bind 0.0.0.0:8000 balancer:app
