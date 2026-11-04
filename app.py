
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


# ---------------- FLASK CONFIGURATION ----------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 2


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

            app.logger.error("Registration database error: %s", error)
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
        return f"Database connection error: {error}", 500

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

        except Error as error:

            app.logger.error("Login database error: %s", error)
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
        return f"Database connection error: {error}", 500

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
        return f"Database connection error: {error}", 500

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

        app.logger.exception(
            "MongoDB notes operation failed."
        )

        return jsonify({
            "error": "Could not access candidate notes."
        }), 500


# ---------------- MONGODB: DELETE CANDIDATE NOTE ----------------

@app.route(
    "/api/candidate/notes/<note_id>",
    methods=["DELETE"]
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
        result = mongo_db["candidate_notes"].delete_one({
            "_id": ObjectId(note_id),
            "candidate_id": current_user["user_id"]
        })

        if result.deleted_count == 0:
            return jsonify({
                "error": "Note not found."
            }), 404

        return jsonify({
            "message": "Note deleted successfully."
        }), 200

    except PyMongoError:

        app.logger.exception(
            "MongoDB note deletion failed."
        )

        return jsonify({
            "error": "Could not delete the note."
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

        app.logger.exception(
            "Semantic job search MongoDB error."
        )

        return jsonify({
            "error": "Semantic search is temporarily unavailable."
        }), 500

    except Exception:

        app.logger.exception(
            "Semantic job search failed."
        )

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
