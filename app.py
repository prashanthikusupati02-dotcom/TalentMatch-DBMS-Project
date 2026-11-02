import os
from flask import Flask, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="job_app_user",
        password=os.getenv("MYSQL_PASSWORD"),
        database="job_matching_db"
    )

@app.route("/")
def home():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                j.job_id,
                j.title,
                j.description,
                j.required_experience,
                j.location,
                j.expiry_date,
                c.company_name
            FROM Job j
            JOIN Recruiter r ON j.recruiter_id = r.recruiter_id
            JOIN Company c ON r.company_id = c.company_id
            WHERE j.expiry_date >= CURRENT_DATE
            ORDER BY j.job_id
        """)
        jobs = cursor.fetchall()

        return render_template("index.html", jobs=jobs)

    except Error as error:
        return f"Database connection error: {error}", 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/matches")
def matches():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM Candidate_Job_Match
            ORDER BY match_percentage DESC, candidate_name
        """)
        results = cursor.fetchall()

        return render_template("matches.html", results=results)

    except Error as error:
        return f"Database connection error: {error}", 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/applications")
def applications():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                a.application_id,
                c.name AS candidate_name,
                j.title AS job_title,
                a.applied_at,
                a.status
            FROM Application a
            JOIN Candidate c ON a.candidate_id = c.candidate_id
            JOIN Job j ON a.job_id = j.job_id
            ORDER BY a.applied_at DESC
        """)
        records = cursor.fetchall()

        return render_template("applications.html", applications=records)

    except Error as error:
        return f"Database connection error: {error}", 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    app.run(debug=True)
