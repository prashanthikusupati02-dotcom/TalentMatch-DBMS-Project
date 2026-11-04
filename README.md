# TalentMatch — Intelligent Job & Talent Matching Platform

## 1. Project Overview

TalentMatch is a database-driven job-matching platform designed to help candidates find suitable job opportunities based on their skills and experience.

The system connects candidates, recruiters, companies, and job opportunities through a relational database. It compares candidate skills with the skills required for jobs and calculates matching percentages.

## 2. Technologies Used

- Python
- Flask
- MySQL 8.0
- HTML
- SQL
- MySQL Connector for Python

## 3. Features

- Display available job listings and company information.
- View candidate-job matching results.
- Calculate skill matching percentages.
- View job applications and their statuses.
- Retrieve information from a MySQL database through a Flask application.
- Use database views, stored procedures, and triggers.
- Maintain data integrity through primary keys, foreign keys, and constraints.

## 4. Project Structure

```text
intelligent_job_matching/
│
├── app.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── matches.html
│   └── applications.html
│
├── documentation/
│   ├── ER_Diagram.mmd
│   ├── 3NF_Schema.md
│   └── SQL_Query_Gallery.sql
│
├── job_matching_db_application.sql
├── job_matching_db_candidate.sql
├── job_matching_db_candidate_skill.sql
├── job_matching_db_company.sql
├── job_matching_db_job.sql
├── job_matching_db_job_skill.sql
├── job_matching_db_recruiter.sql
├── job_matching_db_routines.sql
├── job_matching_db_skill.sql
├── job_matching_db_views.sql
│
├── TalentMatch_Database_Objects.sql
└── TalentMatch_Procedure_Trigger.sql
```

## 5. Database

- Database Name: `job_matching_db`
- DBMS: MySQL 8.0
- Number of Base Tables: 8
- Additional Database Object: `candidate_job_match` view

The database contains the following main entities:

1. Candidate
2. Recruiter
3. Company
4. Job
5. Skill
6. Candidate_Skill
7. Job_Skill
8. Application

The application connects to the MySQL database using Python's MySQL Connector.

The database password is read from the `MYSQL_PASSWORD` environment variable instead of being stored directly in the source code.

## 6. Database Objects

The project includes:

- **View – `candidate_job_match`:** Calculates candidate-job skill matching percentages.
- **Stored Procedure – `Calculate_Match_Score`:** Calculates skill matching and checks experience eligibility for a candidate and job.
- **Trigger – `Before_Application_Insert`:** Prevents applications from being submitted for expired jobs.
- **Indexes:** Improve selected search and filtering operations.
- **Constraints:** Maintain data integrity and prevent invalid records.

## 7. Documentation

Detailed database documentation is available in the `documentation` folder.

- [ER Diagram](documentation/ER_Diagram.mmd)
- [Database Schema and 3NF Documentation](documentation/3NF_Schema.md)
- [SQL Query Gallery](documentation/SQL_Query_Gallery.sql)

The documentation covers:

- Entity relationships and database design.
- Relational schema with primary keys and foreign keys.
- First Normal Form (1NF), Second Normal Form (2NF), and Third Normal Form (3NF).
- SQL queries using joins, subqueries, CTEs, and transactions.
- Views, stored procedures, and triggers.
- Indexing and query execution plans.

## 8. How to Run

### Prerequisites

- Python 3
- MySQL Server 8.0 or later
- MySQL Command Line Client

### Setup Instructions

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Create the `job_matching_db` database in MySQL.
5. Execute the provided SQL scripts to create the tables and database objects. Ensure that tables are created before importing dependent data and creating database objects.
6. Configure the `MYSQL_PASSWORD` environment variable with your MySQL password.
7. Start the Flask application:

   ```bash
   python app.py
   ```

8. Open the following address in your browser:

   `http://127.0.0.1:5000/`

### Notes

- MySQL Server must be running before starting the application.
- The database must be configured before running the Flask application.
- Install the required Python packages using `requirements.txt`.
- The SQL scripts are provided for database setup and reference.

## 9. Academic Project

This project demonstrates relational database design, normalization, SQL programming, database object implementation, and integration of a MySQL database with a Flask web application.

## 10. Conclusion

TalentMatch provides a structured approach to job and talent matching using relational database concepts. It demonstrates how database design, SQL queries, constraints, stored procedures, triggers, and application integration can be used to support a job-matching platform.