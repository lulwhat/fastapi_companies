### FastAPI application for storing companies
<br/>

Runs on *Python 3.12.2*

Uses *FastAPI 0.115.11*, *SQLAlchemy 2.0.39*, *PostgreSQL 17*

Prepared to host with *Docker-compose*

All the requirements are listed in [requirements.txt](/app/requirements.txt)

DB is prepopulated with test data from [db_backup.sql](/app/db_backup.sql)

Task description for the API: [task_description.docx](/task_description.docx)

<br/><br/>

**To use locally run following steps:**

**Start containers:** `docker-compose up --build -d`

**Open in browser to access SwaggerUI:** `http://localhost:8000/docs`

**Shutdown:** `docker-compose down -v`