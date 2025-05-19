## FastAPI application for managing companies

Features:
+ Companies catalogue
+ Buildings with coordinates that companies are registered in
+ Companies phone numbers
+ Searching for companies in an area
+ Companies category tree with search
+ Background tasks for exporting tables data

Stack:
+ Python 3.12.2
+ FastAPI 0.115.11
+ SQLAlchemy 2.0.39
+ PostgreSQL 17
+ RabbitMQ 3.13.7

Prepared to deploy with Docker-compose

Full list of requirements: [requirements.txt](/backend/requirements.txt)

DB is prepopulated with test data with script [load_initial_data.py](/backend/load_initial_data.py)

Full task description: [task_description.docx](/task_description.docx)

<br/>

**To use locally run following steps:**

**Start containers:**
+ Either straight-up execute `./setup` (`.env` will be created from [.env.example](/.env.example) copy)
+ Or create your own `.env` based on [.env.example](/.env.example) and then run `./setup`

**Open in browser to access SwaggerUI:** <http://localhost:8000/api/v1/docs/>

**Shutdown:** `docker-compose down -v`