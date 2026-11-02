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
## How to Run

### Prerequisites
- Python 3
- MySQL Server 8.0 or later

### Setup Instructions

1. Clone or download this repository to your computer.
2. Open a terminal in the project folder.
3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Create the `job_matching_db` database in MySQL.
5. Import the SQL files in the correct order to create the tables and load the sample data. Create the database objects, including the view, stored procedure, and trigger, using the provided SQL scripts.
6. Configure the `MYSQL_PASSWORD` environment variable with your MySQL password. Do not store your database password in the source code.
7. Start the Flask application:

   ```bash
   python app.py
   ```

8. Open `http://127.0.0.1:5000/` in your browser.

### Notes
- The database must be configured before running the application.
- The application requires a running MySQL server.
- The SQL scripts are provided in this repository for database setup and reference.

## Academic Project
This project demonstrates database design, SQL queries, and integration of a relational database with a web application.
