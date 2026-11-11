# TalentMatch – Intelligent Job & Talent Matching Platform

## 1. Project Overview

TalentMatch is a database-driven job and talent matching platform designed to connect candidates with suitable job opportunities based on their skills and experience.

The application uses a relational MySQL database for structured job and candidate information and MongoDB Atlas for candidate notes and semantic job search.

It integrates database management concepts, backend development, authentication, role-based access control, and vector search.

## 2. Technologies Used

### Backend
- Python
- Flask
- MySQL Connector for Python
- PyMongo
- PyJWT
- Werkzeug

### Databases
- MySQL 8.0
- MongoDB Atlas

### AI and Semantic Search
- Sentence Transformers
- all-MiniLM-L6-v2
- MongoDB Vector Search

### Frontend
- HTML
- CSS
- JavaScript
- Flask/Jinja templates

## 3. Features

### Job and Talent Matching
- Display available job listings and company information.
- View candidate-job matching results.
- Calculate skill matching percentages.
- Evaluate candidate experience against job requirements.
- View job applications and their statuses.

### SQL Database Management
- Normalized relational database design (3NF).
- Primary keys, foreign keys, constraints, and indexes.
- SQL joins, subqueries, CTEs, and transactions.
- Views, stored procedures, and triggers.

### Authentication and Access Control
- Candidate and Recruiter registration and login.
- JWT-based authentication.
- Password hashing.
- Role-based access control in the Flask application.
- MySQL database-level RBAC using dedicated Candidate and Recruiter accounts and roles.

### MongoDB Integration
- Store candidate notes in MongoDB Atlas.
- Create, retrieve, update, and delete candidate notes.
- Maintain job vector embeddings in MongoDB.

### AI-Powered Semantic Job Search
- Generate job embeddings using Sentence Transformers.
- Use the all-MiniLM-L6-v2 model to generate 384-dimensional embeddings.
- Perform semantic similarity search using MongoDB Vector Search.
- Retrieve jobs based on the meaning of a search query rather than only exact keyword matches.

## 4. Project Structure

```text
intelligent_job_matching/
│
├── app.py
├── requirements.txt
├── README.md
│
├── semantic_search.py
├── generate_job_vectors.py
│
├── templates/
│   ├── index.html
│   ├── matches.html
│   └── applications.html
│
├── documentation/
│   ├── ER_Diagram.mmd
│   ├── 3NF_Schema.md
│   ├── SQL_Query_Gallery.sql
│   └── MySQL_RBAC.md
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

## 5. MySQL Database Design

- Database Name: `job_matching_db`
- DBMS: MySQL 8.0
- Number of Base Tables: 8
- Additional Database Object: `candidate_job_match` view

The database contains eight main entities:

1. Candidate
2. Recruiter
3. Company
4. Job
5. Skill
6. Candidate_Skill
7. Job_Skill
8. Application

The database implements:
- Primary and foreign key constraints.
- Data integrity constraints.
- Indexes for selected search operations.
- A candidate-job matching view.
- Stored procedures and functions.
- Triggers for application validation.

## 6. Database-Level RBAC

TalentMatch implements MySQL Role-Based Access Control using two database roles:

- `candidate_role`
- `recruiter_role`

Dedicated database accounts are assigned to these roles.

### Candidate Role
- View available jobs, companies, and skills.
- View matching information.
- Manage permitted candidate and skill records.
- Submit applications.

### Recruiter Role
- View candidate information and skills.
- Create, update, and delete job postings.
- Manage job skills.
- View applications and update application statuses.

The database permissions were tested using separate MySQL accounts. Unauthorized UPDATE operations were successfully denied.

Detailed implementation and test results are available in [MySQL RBAC Documentation](documentation/MySQL_RBAC.md).

**Note:** These permissions are table-level permissions. Individual candidate record ownership is additionally handled through application-level authorization where implemented.

## 7. MongoDB Atlas Integration

MongoDB Atlas is used for storing additional application data.

Database: `talentmatch_db`

Collections:
- `candidate_notes`
- `job_vectors`

### Candidate Notes
The application supports CRUD operations:
- Create candidate notes.
- Retrieve candidate notes.
- Update existing notes.
- Delete notes.

### Job Vectors
Job descriptions are converted into numerical embeddings and stored in MongoDB.

A vector search index named `job_vector_index` is configured with:
- Embedding dimensions: 384
- Similarity metric: cosine
- Embedding model: all-MiniLM-L6-v2

## 8. Semantic Job Search

TalentMatch includes an AI-powered semantic search feature.

The system uses Sentence Transformers to convert job descriptions and search queries into embeddings.

MongoDB Atlas Vector Search compares these embeddings to identify semantically relevant job opportunities.

API endpoint:

`/api/jobs/semantic-search`

This allows candidates to discover relevant jobs even when their search query does not use exactly the same words as a job description.

## 9. Authentication and API Access

The Flask backend implements:
- JWT-based authentication.
- Password hashing.
- Candidate and Recruiter roles.
- Protected application routes.
- Role-based API authorization.

Important API functionality includes:

| API | Purpose |
|---|---|
| `/api/me` | Retrieve authenticated user information |
| `/api/candidate/notes` | Retrieve or create candidate notes |
| `/api/candidate/notes/<note_id>` | Update or delete a candidate note |
| `/api/jobs/semantic-search` | Search jobs using semantic similarity |

## 10. How to Run the Project

### Prerequisites

- Python 3
- MySQL Server 8.0 or later
- MongoDB Atlas account
- MySQL Command Line Client

### Step 1: Clone the Repository

```bash
git clone https://github.com/prashanthikusupati02-dotcom/TalentMatch-DBMS-Project.git
cd TalentMatch-DBMS-Project
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure MySQL

Create the `job_matching_db` database and execute the provided SQL scripts in the appropriate dependency order.

Ensure that the tables and required database objects are created before starting the application.

### Step 4: Configure Environment Variables

Set the following environment variables:

- `MYSQL_PASSWORD`
- `JWT_SECRET_KEY`
- `MONGO_URI`

Use your own credentials and secrets. Do not commit passwords, connection strings, or secret keys to GitHub.

### Step 5: Configure MongoDB Atlas

Configure your MongoDB Atlas connection and ensure that the required collections and vector search index are available.

For semantic search, generate and store the job embeddings using the provided vector generation script.

### Step 6: Start the Flask Application

```bash
python app.py
```

### Step 7: Open the Application

Visit:

`http://127.0.0.1:5000/`

## 11. Documentation

Detailed documentation is available in the `documentation` directory.

- [ER Diagram](documentation/ER_Diagram.mmd)
- [Database Schema and 3NF](documentation/3NF_Schema.md)
- [SQL Query Gallery](documentation/SQL_Query_Gallery.sql)
- [MySQL Database-Level RBAC](documentation/MySQL_RBAC.md)

## 12. Academic Project

TalentMatch demonstrates the practical application of:

- Relational database design and normalization.
- SQL queries and database programming.
- Database constraints, transactions, views, procedures, and triggers.
- NoSQL database integration.
- Backend API development.
- Authentication and role-based access control.
- Semantic search using vector embeddings.

## 13. Conclusion

TalentMatch combines relational database management, NoSQL storage, backend development, authentication, and semantic search to provide an integrated job and talent matching platform.

The project demonstrates how database concepts and modern application technologies can be combined to build a practical job-matching system.