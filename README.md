# TalentMatch — Intelligent Job & Talent Matching Platform

## Project Overview
TalentMatch is a database-driven job-matching platform designed to help candidates find suitable job opportunities based on their skills, education, and experience.

## Technologies Used
- Python
- Flask
- MySQL
- HTML
- SQL

## Features
- Display available job listings and company information.
- View candidate-job matching results.
- View job applications and their statuses.
- Retrieve information from a MySQL database through a Flask application.

## Project Structure
```text
intelligent_job_matching/
├── app.py
├── templates/
│   ├── index.html
│   ├── matches.html
│   └── applications.html
└── README.md
```

## Database
The application connects to the `job_matching_db` MySQL database.

The database connection password is read from the `MYSQL_PASSWORD` environment variable.

## How to Run
1. Install Python and MySQL.
2. Install the required Python packages.
3. Configure the `MYSQL_PASSWORD` environment variable.
4. Ensure the `job_matching_db` database and its required tables exist.
5. Run the application using `python app.py`.
6. Open `http://127.0.0.1:5000/` in a browser.

## Academic Project
This project demonstrates database design, SQL queries, and integration of a relational database with a web application.

## Documentation

Detailed project documentation is available in the `documentation` folder.

- [ER Diagram](documentation/ER_Diagram.mmd)
- [Database Schema and 3NF Documentation](documentation/3NF_Schema.md)
- [SQL Query Gallery](documentation/SQL_Query_Gallery.sql)

The documentation covers:
- Entity relationships and database design.
- Eight relational tables and their constraints.
- First, Second and Third Normal Forms.
- SQL queries using joins, subqueries, CTEs and transactions.
- Views, stored procedures and triggers.
- Indexing and query execution plans.