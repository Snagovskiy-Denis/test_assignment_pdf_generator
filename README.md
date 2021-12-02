
# Introduction

This project realized [that](https://github.com/smenateam/assignments/tree/master/backend) test assignment

Main Goal: to show that I can implement basic application with asynchronous workers

Project main stack:

    - Django & Django Rest Framework
    - Celery
    - PostgreSQL
    - Redis

![][.github/arch.png]


# How to run

1. Create and activate virtual environment, install requirements

```bash
python -m venv ./venv && source ./venv/bin/activate
pip install -r requirements.txt
```

2. Run infrastructure (PostgreSQL, Redis, Celery, wkhtmltopdf):

```bash
docker-compose up -d
```

3. Run Django test-server:

```bash
./manage.py runserver
```
