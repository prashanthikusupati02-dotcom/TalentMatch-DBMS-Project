
import os
import datetime
from functools import wraps

import jwt
import mysql.connector

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from sentence_transformers import SentenceTransformer

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, make_response, jsonify
)

from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

# ---------------- FLASK CONFIGURATION ----------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 2
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]
        }
    },
    supports_credentials=True
)

# ---------------- MONGODB CONFIGURATION ----------------

MONGO_URI = os.getenv("MONGO_URI")

mongo_client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
) if MONGO_URI else None

mongo_db = mongo_client["talentmatch_db"] if mongo_client else None


# ---------------- SEMANTIC SEARCH MODEL ----------------

embedding_model = None


def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return embedding_model


# ---------------- MYSQL CONNECTION ----------------

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="job_app_user",
        password=os.getenv("MYSQL_PASSWORD"),
        database="job_matching_db"
    )


# ---------------- JWT AUTHENTICATION ----------------

def generate_token(user_id, email, role):
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def token_required(roles=None):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            token = request.cookies.get("access_token")

            if not token:
                flash("Please log in first.")
                return redirect(url_for("login"))

            try:
                data = jwt.decode(
                    token,
                    JWT_SECRET_KEY,
                    algorithms=[JWT_ALGORITHM]
                )

            except jwt.ExpiredSignatureError:

                flash("Your session has expired. Please log in again.")

                response = make_response(
                    redirect(url_for("login"))
                )

                response.delete_cookie("access_token")
                return response

            except jwt.InvalidTokenError:

                flash("Invalid login session.")

                response = make_response(
                    redirect(url_for("login"))
                )

                response.delete_cookie("access_token")
                return response

            if roles and data["role"] not in roles:
                return "Access denied: insufficient permissions.", 403

            return function(data, *args, **kwargs)

        return wrapper

    return decorator

# ---------------- API AUTHENTICATION ----------------

def api_token_required(roles=None):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            auth_header = request.headers.get("Authorization", "")

            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
            else:
                token = request.cookies.get("access_token")

            if not token:
                return jsonify({
                    "error": "Authentication token required."
                }), 401

            try:
                data = jwt.decode(
                    token,
                    JWT_SECRET_KEY,
                    algorithms=[JWT_ALGORITHM]
                )

            except jwt.ExpiredSignatureError:
                return jsonify({
                    "error": "Your session has expired. Please log in again."
                }), 401
            except jwt.InvalidTokenError:
                return jsonify({
                    "error": "Invalid authentication token."
                }), 401

            if roles and data.get("role") not in roles:
                return jsonify({
                    "error": "You do not have permission to access this resource."
                }), 403

            return function(data, *args, **kwargs)

        return wrapper

    return decorator
# ---------------- HOME PAGE ----------------

@app.route("/")
def home():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT j.job_id, j.title, j.description,
                   j.required_experience, j.location,
                   j.expiry_date, c.company_name
            FROM Job j
            JOIN Recruiter r ON j.recruiter_id = r.recruiter_id
            JOIN Company c ON r.company_id = c.company_id
            WHERE j.expiry_date >= CURRENT_DATE
            ORDER BY j.job_id
        """)

        jobs = cursor.fetchall()

        return render_template("index.html", jobs=jobs)

    except Error as error:
        app.logger.exception("Home page database error.")
        return f"Database connection error: {error}", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- USER REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    connection = None
    cursor = None

    if request.method == "POST":

        role = request.form.get("role")
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if role not in ("candidate", "recruiter"):
            flash("Invalid account type.")
            return redirect(url_for("register"))

        if not name or not email or len(password) < 8:
            flash("Enter valid details. Password must be at least 8 characters.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            if role == "candidate":

                experience = request.form.get("experience_years", "0")

                try:
                    experience = float(experience)

                    if not 0 <= experience <= 99.9:
                        raise ValueError

                except ValueError:
                    flash("Enter valid experience between 0 and 99.9.")
                    return redirect(url_for("register"))

                cursor.execute("""
                    INSERT INTO Candidate
                    (name, email, password_hash, experience_years)
                    VALUES (%s, %s, %s, %s)
                """, (name, email, password_hash, experience))

            else:

                company_id = request.form.get("company_id")

                if not company_id or not company_id.isdigit():
                    flash("Please select a valid company.")
                    return redirect(url_for("register"))

                cursor.execute(
                    "SELECT company_id FROM Company WHERE company_id = %s",
                    (int(company_id),)
                )

                if not cursor.fetchone():
                    flash("Selected company does not exist.")
                    return redirect(url_for("register"))

                cursor.execute("""
                    INSERT INTO Recruiter
                    (company_id, name, email, password_hash)
                    VALUES (%s, %s, %s, %s)
                """, (int(company_id), name, email, password_hash))

            connection.commit()

            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))

        except mysql.connector.IntegrityError:

            if connection:
                connection.rollback()

            flash("This email is already registered.")

        except Error as error:

            if connection:
                connection.rollback()

            app.logger.exception("Registration database error.")
            flash("Registration could not be completed.")

        finally:

            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT company_id, company_name
            FROM Company
            ORDER BY company_name
        """)

        companies = cursor.fetchall()

        return render_template(
            "register.html",
            companies=companies
        )

    except Error as error:
        app.logger.exception("Company retrieval error.")
        return f"Database connection error: {error}", 500

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ---------------- JSON LOGIN API ----------------

@app.route("/api/auth/login", methods=["POST"])
def api_login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required."}), 400

    email = data.get("email", "")
    password = data.get("password", "")
    role = data.get("role")

    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Valid email is required."}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"error": "Password is required."}), 400

    if role not in ("candidate", "recruiter"):
        return jsonify({"error": "Invalid account type."}), 400

    table = "Candidate" if role == "candidate" else "Recruiter"

    id_column = (
        "candidate_id" if role == "candidate"
        else "recruiter_id"
    )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            f"SELECT {id_column} AS user_id, email, password_hash "
            f"FROM {table} WHERE email = %s",
            (email.strip().lower(),)
        )

        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "error": "Invalid email, password or account type."
            }), 401

        token = generate_token(
            user["user_id"],
            user["email"],
            role
        )

        return jsonify({
            "message": "Login successful.",
            "access_token": token,
            "token_type": "Bearer",
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "role": role
            }
        }), 200

    except Error:
        app.logger.exception("JSON login API failed.")

        return jsonify({
            "error": "Login could not be completed."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- USER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role")

        if role not in ("candidate", "recruiter"):
            flash("Invalid account type.")
            return redirect(url_for("login"))

        table = "Candidate" if role == "candidate" else "Recruiter"

        id_column = (
            "candidate_id" if role == "candidate"
            else "recruiter_id"
        )

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                f"SELECT {id_column} AS user_id, email, password_hash "
                f"FROM {table} WHERE email = %s",
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):

                token = generate_token(
                    user["user_id"],
                    user["email"],
                    role
                )

                response = make_response(
                    redirect(url_for("home"))
                )

                response.set_cookie(
                    "access_token",
                    token,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=JWT_EXPIRY_HOURS * 3600
                )

                return response

            flash("Invalid email, password or account type.")

        except Error:

            app.logger.exception("Login database error.")
            flash("Login could not be completed.")

        finally:

            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    response = make_response(
        redirect(url_for("login"))
    )

    response.delete_cookie("access_token")

    flash("You have been logged out.")

    return response


# ---------------- JOB MATCHES ----------------

@app.route("/matches")
@token_required(roles=["candidate", "recruiter"])
def matches(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM Candidate_Job_Match
            ORDER BY match_percentage DESC, candidate_name
        """)

        results = cursor.fetchall()

        return render_template(
            "matches.html",
            results=results
        )

    except Error as error:
        app.logger.exception("Job matches database error.")
        return f"Database connection error: {error}", 500

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- CANDIDATE: MY APPLICATIONS ----------------

@app.route("/my-applications")
@token_required(roles=["candidate"])
def my_applications(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT a.application_id,
                   j.title AS job_title,
                   j.location,
                   a.applied_at,
                   a.status
            FROM Application a
            JOIN Job j ON a.job_id = j.job_id
            WHERE a.candidate_id = %s
            ORDER BY a.applied_at DESC
        """, (current_user["user_id"],))

        records = cursor.fetchall()

        return render_template(
            "my_applications.html",
            applications=records
        )

    except Error:
        app.logger.exception("Candidate applications database error.")
        return "Could not load your applications.", 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
# ---------------- RECRUITER APPLICATIONS ----------------

@app.route("/applications")
@token_required(roles=["recruiter"])
def applications(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT a.application_id,
                   c.name AS candidate_name,
                   j.title AS job_title,
                   a.applied_at, a.status
            FROM Application a
            JOIN Candidate c ON a.candidate_id = c.candidate_id
            JOIN Job j ON a.job_id = j.job_id
            ORDER BY a.applied_at DESC
        """)

        records = cursor.fetchall()

        return render_template(
            "applications.html",
            applications=records
        )

    except Error as error:
        app.logger.exception("Applications database error.")
        return f"Database connection error: {error}", 500

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- CANDIDATE PROFILE API ----------------

@app.route("/api/candidate/profile", methods=["GET", "PUT"])
@api_token_required(roles=["candidate"])
def candidate_profile(current_user):

    connection = None
    cursor = None
    candidate_id = current_user["user_id"]

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "GET":

            cursor.execute("""
                SELECT candidate_id, name, email, experience_years
                FROM Candidate
                WHERE candidate_id = %s
            """, (candidate_id,))

            profile = cursor.fetchone()

            if not profile:
                return jsonify({"error": "Candidate not found."}), 404

            return jsonify({"profile": profile}), 200

        data = request.get_json(silent=True) or {}

        name = data.get("name")
        email = data.get("email")
        experience = data.get("experience_years")

        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "Valid name is required."}), 400

        if not isinstance(email, str) or not email.strip() or "@" not in email:
            return jsonify({"error": "Valid email is required."}), 400

        try:
            experience = float(experience)
            if not 0 <= experience <= 99.9:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({
                "error": "Experience must be between 0 and 99.9."
            }), 400

        cursor.execute("""
            UPDATE Candidate
            SET name = %s, email = %s, experience_years = %s
            WHERE candidate_id = %s
        """, (name.strip(), email.strip().lower(), experience, candidate_id))

        connection.commit()

        return jsonify({
            "message": "Candidate profile updated successfully."
        }), 200

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "This email is already registered."}), 409

    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Candidate profile API failed.")
        return jsonify({"error": "Unable to process candidate profile."}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
# ---------------- RECRUITER PROFILE API ----------------

@app.route("/api/recruiter/profile", methods=["GET", "PUT"])
@api_token_required(roles=["recruiter"])
def recruiter_profile(current_user):

    connection = None
    cursor = None
    recruiter_id = current_user["user_id"]

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "GET":

            cursor.execute("""
                SELECT
                    r.recruiter_id,
                    r.name,
                    r.email,
                    c.company_id,
                    c.company_name,
                    c.industry,
                    c.location
                FROM Recruiter r
                JOIN Company c ON r.company_id = c.company_id
                WHERE r.recruiter_id = %s
            """, (recruiter_id,))

            profile = cursor.fetchone()

            if not profile:
                return jsonify({"error": "Recruiter not found."}), 404

            return jsonify({"profile": profile}), 200

        data = request.get_json(silent=True) or {}

        name = data.get("name")
        email = data.get("email")

        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "Valid name is required."}), 400

        if not isinstance(email, str) or not email.strip() or "@" not in email:
            return jsonify({"error": "Valid email is required."}), 400

        cursor.execute("""
            UPDATE Recruiter
            SET name = %s, email = %s
            WHERE recruiter_id = %s
        """, (name.strip(), email.strip().lower(), recruiter_id))

        connection.commit()

        return jsonify({
            "message": "Recruiter profile updated successfully."
        }), 200

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()

        return jsonify({"error": "This email is already registered."}), 409

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Recruiter profile API failed.")

        return jsonify({
            "error": "Unable to process recruiter profile."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- JOB CREATION API ----------------

@app.route("/api/jobs", methods=["POST"])
@api_token_required(roles=["recruiter"])
def create_job(current_user):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required."}), 400

    title = data.get("title")
    description = data.get("description", "")
    location = data.get("location", "")
    experience = data.get("required_experience", 0)

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Job title is required."}), 400

    if len(title.strip()) > 150:
        return jsonify({"error": "Job title must be at most 150 characters."}), 400

    try:
        experience = float(experience)
        if not 0 <= experience <= 99.9:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid required experience."}), 400

    posted_date = datetime.date.today()

    try:
        expiry_date = datetime.date.fromisoformat(data.get("expiry_date", ""))
    except (TypeError, ValueError):
        return jsonify({
            "error": "Provide a valid expiry_date in YYYY-MM-DD format."
        }), 400

    if expiry_date < posted_date:
        return jsonify({
            "error": "Expiry date cannot be before today's date."
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO Job (
                recruiter_id,
                title,
                description,
                required_experience,
                location,
                posted_date,
                expiry_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            current_user["user_id"],
            title.strip(),
            description,
            experience,
            location,
            posted_date,
            expiry_date
        ))

        connection.commit()
        job_id = cursor.lastrowid

        return jsonify({
            "message": "Job created successfully.",
            "job_id": job_id
        }), 201

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Job creation API failed.")

        return jsonify({"error": "Unable to create job."}), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- VIEW JOBS API ----------------

@app.route("/api/jobs", methods=["GET"])
@api_token_required()
def get_jobs(current_user):

    connection = None
    cursor = None

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
                j.posted_date,
                j.expiry_date,
                c.company_name
            FROM Job j
            JOIN Recruiter r ON j.recruiter_id = r.recruiter_id
            JOIN Company c ON r.company_id = c.company_id
            WHERE j.expiry_date >= CURRENT_DATE
            ORDER BY j.posted_date DESC
        """)

        jobs = cursor.fetchall()

        for job in jobs:
            job["required_experience"] = float(
                job["required_experience"]
            )
            job["posted_date"] = job["posted_date"].isoformat()
            job["expiry_date"] = job["expiry_date"].isoformat()

        return jsonify({"jobs": jobs}), 200

    except Error:
        app.logger.exception("View jobs API failed.")

        return jsonify({"error": "Unable to retrieve jobs."}), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- EDIT JOB API ----------------

@app.route("/api/jobs/<int:job_id>", methods=["PUT"])
@api_token_required(roles=["recruiter"])
def update_job(current_user, job_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required."}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM Job
            WHERE job_id = %s AND recruiter_id = %s
        """, (job_id, current_user["user_id"]))

        job = cursor.fetchone()

        if not job:
            return jsonify({
                "error": "Job not found or access denied."
            }), 404

        title = data.get("title", job["title"])
        description = data.get("description", job["description"])
        location = data.get("location", job["location"])
        experience = data.get(
            "required_experience",
            job["required_experience"]
        )
        expiry_value = data.get("expiry_date", job["expiry_date"])

        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "Valid job title is required."}), 400

        if len(title.strip()) > 150:
            return jsonify({"error": "Job title is too long."}), 400

        if description is not None and not isinstance(description, str):
            return jsonify({"error": "Invalid description."}), 400

        if location is not None and not isinstance(location, str):
            return jsonify({"error": "Invalid location."}), 400

        if location and len(location) > 150:
            return jsonify({"error": "Location is too long."}), 400

        try:
            experience = float(experience)
            if not 0 <= experience <= 99.9:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid required experience."}), 400

        try:
            if isinstance(expiry_value, datetime.date):
                expiry_date = expiry_value
            else:
                expiry_date = datetime.date.fromisoformat(expiry_value)
        except (TypeError, ValueError):
            return jsonify({
                "error": "Expiry date must use YYYY-MM-DD format."
            }), 400

        if expiry_date < job["posted_date"]:
            return jsonify({
                "error": "Expiry date cannot be before the posted date."
            }), 400

        cursor.execute("""
            UPDATE Job
            SET title = %s,
                description = %s,
                required_experience = %s,
                location = %s,
                expiry_date = %s
            WHERE job_id = %s AND recruiter_id = %s
        """, (
            title.strip(),
            description,
            experience,
            location,
            expiry_date,
            job_id,
            current_user["user_id"]
        ))

        connection.commit()

        return jsonify({
            "message": "Job updated successfully.",
            "job_id": job_id
        }), 200

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Job update API failed.")

        return jsonify({"error": "Unable to update job."}), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- DELETE JOB API ----------------

@app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
@api_token_required(roles=["recruiter"])
def delete_job(current_user, job_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT job_id
            FROM Job
            WHERE job_id = %s AND recruiter_id = %s
        """, (job_id, current_user["user_id"]))

        if not cursor.fetchone():
            return jsonify({
                "error": "Job not found or access denied."
            }), 404

        cursor.execute("""
            SELECT application_id
            FROM Application
            WHERE job_id = %s
            LIMIT 1
        """, (job_id,))

        if cursor.fetchone():
            return jsonify({
                "error": "Cannot delete this job because candidates have already applied."
            }), 409

        cursor.execute("""
            DELETE FROM Job_Skill
            WHERE job_id = %s
        """, (job_id,))

        cursor.execute("""
            DELETE FROM Job
            WHERE job_id = %s AND recruiter_id = %s
        """, (job_id, current_user["user_id"]))

        connection.commit()

        return jsonify({
            "message": "Job deleted successfully.",
            "job_id": job_id
        }), 200

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Job deletion API failed.")

        return jsonify({
            "error": "Unable to delete job."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- CANDIDATE JOB APPLICATION API ----------------

@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
@api_token_required(roles=["candidate"])
def apply_for_job(current_user, job_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check whether the job exists and is still active.
        cursor.execute("""
            SELECT job_id
            FROM Job
            WHERE job_id = %s
              AND expiry_date >= CURRENT_DATE
        """, (job_id,))

        if not cursor.fetchone():
            return jsonify({
                "error": "Job not found or application deadline has passed."
            }), 404

        # Prevent duplicate applications.
        cursor.execute("""
            SELECT application_id
            FROM Application
            WHERE candidate_id = %s AND job_id = %s
        """, (current_user["user_id"], job_id))

        if cursor.fetchone():
            return jsonify({
                "error": "You have already applied for this job."
            }), 409

        cursor.execute("""
            INSERT INTO Application (candidate_id, job_id)
            VALUES (%s, %s)
        """, (current_user["user_id"], job_id))

        connection.commit()

        application_id = cursor.lastrowid

        return jsonify({
            "message": "Job application submitted successfully.",
            "application_id": application_id,
            "job_id": job_id,
            "status": "Applied"
        }), 201

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()

        return jsonify({
            "error": "Application could not be submitted. Please check your account and job."
        }), 409

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Job application API failed.")

        return jsonify({
            "error": "Unable to submit job application."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- CANDIDATE APPLICATIONS LIST API ----------------

@app.route("/api/candidate/applications", methods=["GET"])
@api_token_required(roles=["candidate"])
def candidate_applications_api(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                a.application_id,
                a.job_id,
                j.title AS job_title,
                c.company_name,
                j.location,
                a.applied_at,
                a.status
            FROM Application a
            JOIN Job j ON a.job_id = j.job_id
            JOIN Recruiter r ON j.recruiter_id = r.recruiter_id
            JOIN Company c ON r.company_id = c.company_id
            WHERE a.candidate_id = %s
            ORDER BY a.applied_at DESC
        """, (current_user["user_id"],))

        applications = cursor.fetchall()

        for application in applications:
            if application["applied_at"]:
                application["applied_at"] = (
                    application["applied_at"].isoformat()
                )

        return jsonify({
            "applications": applications,
            "total_applications": len(applications)
        }), 200

    except Error:
        app.logger.exception("Candidate applications API failed.")

        return jsonify({
            "error": "Unable to retrieve candidate applications."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- CANDIDATE MATCH RESULTS API ----------------

@app.route("/api/candidate/matches", methods=["GET"])
@api_token_required(roles=["candidate"])
def candidate_match_results(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                candidate_id,
                candidate_name,
                job_id,
                job_title,
                total_required_skills,
                matched_skills,
                match_percentage
            FROM candidate_job_match
            WHERE candidate_id = %s
            ORDER BY match_percentage DESC
        """, (current_user["user_id"],))

        matches = cursor.fetchall()

        for match in matches:
            if match["match_percentage"] is not None:
                match["match_percentage"] = float(
                    match["match_percentage"]
                )

        return jsonify({
            "matches": matches,
            "total_matches": len(matches)
        }), 200

    except Error:
        app.logger.exception("Candidate match results API failed.")

        return jsonify({
            "error": "Unable to retrieve candidate match results."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- RECRUITER COMPANY API ----------------

@app.route("/api/recruiter/company", methods=["GET", "PUT"])
@api_token_required(roles=["recruiter"])
def recruiter_company(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT company_id
            FROM Recruiter
            WHERE recruiter_id = %s
        """, (current_user["user_id"],))

        recruiter = cursor.fetchone()

        if not recruiter:
            return jsonify({"error": "Recruiter not found."}), 404

        company_id = recruiter["company_id"]

        if request.method == "GET":

            cursor.execute("""
                SELECT company_id, company_name, industry, location
                FROM Company
                WHERE company_id = %s
            """, (company_id,))

            company = cursor.fetchone()

            if not company:
                return jsonify({"error": "Company not found."}), 404

            return jsonify({"company": company}), 200

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "JSON request body is required."}), 400

        company_name = data.get("company_name")
        industry = data.get("industry")
        location = data.get("location")

        if not isinstance(company_name, str) or not company_name.strip():
            return jsonify({"error": "Valid company name is required."}), 400

        if len(company_name.strip()) > 150:
            return jsonify({"error": "Company name is too long."}), 400

        if industry is not None and not isinstance(industry, str):
            return jsonify({"error": "Invalid industry."}), 400

        if location is not None and not isinstance(location, str):
            return jsonify({"error": "Invalid location."}), 400

        cursor.execute("""
            UPDATE Company
            SET company_name = %s,
                industry = %s,
                location = %s
            WHERE company_id = %s
        """, (
            company_name.strip(),
            industry,
            location,
            company_id
        ))

        connection.commit()

        return jsonify({
            "message": "Company profile updated successfully.",
            "company_id": company_id
        }), 200

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()

        return jsonify({
            "error": "This company name is already registered."
        }), 409

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("Recruiter company API failed.")

        return jsonify({
            "error": "Unable to process company profile."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- CURRENT USER API ----------------

@app.route("/api/me")
@token_required()
def current_user(current_user):

    return jsonify({
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"]
    })


# ---------------- MONGODB: CANDIDATE NOTES ----------------

@app.route("/api/candidate/notes", methods=["GET", "POST"])
@token_required(roles=["candidate"])
def candidate_notes(current_user):

    if mongo_db is None:
        return jsonify({
            "error": "MongoDB is not configured."
        }), 503

    try:
        notes_collection = mongo_db["candidate_notes"]
        candidate_id = current_user["user_id"]

        if request.method == "POST":

            data = request.get_json(silent=True) or {}
            note = data.get("note", "").strip()

            if not note:
                return jsonify({
                    "error": "Note cannot be empty."
                }), 400

            if len(note) > 2000:
                return jsonify({
                    "error": "Note cannot exceed 2000 characters."
                }), 400

            result = notes_collection.insert_one({
                "candidate_id": candidate_id,
                "note": note,
                "created_at": datetime.datetime.now(
                    datetime.timezone.utc
                )
            })

            return jsonify({
                "message": "Note saved successfully.",
                "note_id": str(result.inserted_id)
            }), 201

        notes = list(
            notes_collection.find({
                "candidate_id": candidate_id
            }).sort("created_at", -1)
        )

        for item in notes:
            item["_id"] = str(item["_id"])

        return jsonify({
            "notes": notes
        }), 200

    except PyMongoError:

        app.logger.exception("MongoDB notes operation failed.")

        return jsonify({
            "error": "Could not access candidate notes."
        }), 500

# ---------------- RECRUITER: UPDATE APPLICATION STATUS ----------------

@app.route("/applications/<int:application_id>/status", methods=["POST"])
@token_required(roles=["recruiter"])
def update_application_status(current_user, application_id):

    allowed_statuses = {
        "Applied",
        "Under Review",
        "Shortlisted",
        "Rejected"
    }

    new_status = request.form.get("status", "").strip()

    if new_status not in allowed_statuses:
        flash("Invalid application status.")
        return redirect(url_for("applications"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE Application
            SET status = %s
            WHERE application_id = %s
        """, (new_status, application_id))

        if cursor.rowcount == 0:
            flash("Application not found or status unchanged.")
        else:
            connection.commit()
            flash("Application status updated successfully.")

        return redirect(url_for("applications"))

    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Application status update failed.")
        return "Could not update application status.", 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# ---------------- RECRUITER APPLICATIONS LIST API ----------------

@app.route("/api/recruiter/applications", methods=["GET"])
@api_token_required(roles=["recruiter"])
def recruiter_applications_api(current_user):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                a.application_id,
                a.candidate_id,
                c.name AS candidate_name,
                c.email AS candidate_email,
                a.job_id,
                j.title AS job_title,
                a.applied_at,
                a.status
            FROM Application a
            JOIN Candidate c ON a.candidate_id = c.candidate_id
            JOIN Job j ON a.job_id = j.job_id
            WHERE j.recruiter_id = %s
            ORDER BY a.applied_at DESC
        """, (current_user["user_id"],))

        applications = cursor.fetchall()

        for application in applications:
            if application["applied_at"]:
                application["applied_at"] = (
                    application["applied_at"].isoformat()
                )

        return jsonify({
            "applications": applications,
            "total_applications": len(applications)
        }), 200

    except Error:
        app.logger.exception("Recruiter applications API failed.")

        return jsonify({
            "error": "Unable to retrieve recruiter applications."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ---------------- RECRUITER APPLICATION STATUS API ----------------

@app.route(
    "/api/recruiter/applications/<int:application_id>/status",
    methods=["PUT"]
)
@api_token_required(roles=["recruiter"])
def api_update_application_status(current_user, application_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required."}), 400

    new_status = data.get("status")

    allowed_statuses = {
        "Applied",
        "Under Review",
        "Shortlisted",
        "Rejected"
    }

    if not isinstance(new_status, str) or new_status.strip() not in allowed_statuses:
        return jsonify({"error": "Invalid application status."}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Verify that this application belongs to a job
        # posted by the logged-in recruiter.
        cursor.execute("""
            SELECT a.application_id
            FROM Application a
            JOIN Job j ON a.job_id = j.job_id
            WHERE a.application_id = %s
              AND j.recruiter_id = %s
        """, (application_id, current_user["user_id"]))

        if not cursor.fetchone():
            return jsonify({
                "error": "Application not found or access denied."
            }), 404

        cursor.execute("""
            UPDATE Application
            SET status = %s
            WHERE application_id = %s
        """, (new_status.strip(), application_id))

        connection.commit()

        return jsonify({
            "message": "Application status updated successfully.",
            "application_id": application_id,
            "status": new_status.strip()
        }), 200

    except Error:
        if connection:
            connection.rollback()

        app.logger.exception("API application status update failed.")

        return jsonify({
            "error": "Unable to update application status."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ---------------- MONGODB: UPDATE / DELETE CANDIDATE NOTE ----------------

@app.route(
    "/api/candidate/notes/<note_id>",
    methods=["PUT", "DELETE"]
)
@token_required(roles=["candidate"])
def delete_candidate_note(current_user, note_id):

    if mongo_db is None:
        return jsonify({
            "error": "MongoDB is not configured."
        }), 503

    if not ObjectId.is_valid(note_id):
        return jsonify({
            "error": "Invalid note ID."
        }), 400

    try:
        notes_collection = mongo_db["candidate_notes"]

        note_filter = {
            "_id": ObjectId(note_id),
            "candidate_id": current_user["user_id"]
        }

        if request.method == "PUT":

            data = request.get_json(silent=True) or {}
            note = data.get("note", "").strip()

            if not note:
                return jsonify({
                    "error": "Note cannot be empty."
                }), 400

            if len(note) > 2000:
                return jsonify({
                    "error": "Note cannot exceed 2000 characters."
                }), 400

            result = notes_collection.update_one(
                note_filter,
                {"$set": {"note": note}}
            )

            if result.matched_count == 0:
                return jsonify({
                    "error": "Note not found."
                }), 404

            return jsonify({
                "message": "Note updated successfully."
            }), 200

        result = notes_collection.delete_one(note_filter)

        if result.deleted_count == 0:
            return jsonify({
                "error": "Note not found."
            }), 404

        return jsonify({
            "message": "Note deleted successfully."
        }), 200

    except PyMongoError:

        app.logger.exception("MongoDB note operation failed.")

        return jsonify({
            "error": "Could not process candidate note."
        }), 500


# ---------------- MONGODB: SEMANTIC JOB SEARCH ----------------

@app.route("/api/jobs/semantic-search", methods=["POST"])
@token_required(roles=["candidate"])
def semantic_job_search(current_user):

    if mongo_db is None:
        return jsonify({
            "error": "MongoDB is not configured."
        }), 503

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "error": "Please enter a job search query."
        }), 400

    if len(query) > 500:
        return jsonify({
            "error": "Search query cannot exceed 500 characters."
        }), 400

    try:
        model = get_embedding_model()
        query_embedding = model.encode(query).tolist()

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "job_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 20,
                    "limit": 5
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "job_id": 1,
                    "title": 1,
                    "description": 1,
                    "location": 1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    }
                }
            }
        ]

        results = list(
            mongo_db["job_vectors"].aggregate(pipeline)
        )

        return jsonify({
            "query": query,
            "total_results": len(results),
            "results": results
        }), 200

    except PyMongoError:

        app.logger.exception("Semantic search MongoDB error.")

        return jsonify({
            "error": "Semantic search is temporarily unavailable."
        }), 500

    except Exception:

        app.logger.exception("Semantic job search failed.")

        return jsonify({
            "error": "Could not complete semantic job search."
        }), 500


# ---------------- APPLICATION START ----------------

if __name__ == "__main__":

    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is missing."
        )

    app.run(debug=False)
