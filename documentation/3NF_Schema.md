
# TalentMatch – Database Schema and 3NF Documentation

## 1. Database Overview

Database Name: `job_matching_db`

DBMS: MySQL 8.0

TalentMatch is an intelligent job-matching system that connects candidates with recruiters and job opportunities. It compares candidate skills with the skills required by jobs and calculates a matching percentage.

The database contains eight base tables and one view.

## 2. Relational Schema

### 2.1 Candidate

| Column | Data Type | Key / Constraint |
|---|---|---|
| candidate_id | INT | Primary Key, Auto Increment |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(150) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| experience_years | DECIMAL(4,1) | NOT NULL, DEFAULT 0.0 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

Additional constraints:
- Experience must be non-negative.
- Index: `idx_candidate_experience`.

### 2.2 Recruiter

| Column | Data Type | Key / Constraint |
|---|---|---|
| recruiter_id | INT | Primary Key, Auto Increment |
| company_id | INT | Foreign Key |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(150) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |

Foreign key:
- `company_id` references `company(company_id)`.
- ON DELETE RESTRICT.

### 2.3 Company

| Column | Data Type | Key / Constraint |
|---|---|---|
| company_id | INT | Primary Key, Auto Increment |
| company_name | VARCHAR(150) | UNIQUE, NOT NULL |
| industry | VARCHAR(100) | NULL allowed |
| location | VARCHAR(150) | NULL allowed |

### 2.4 Job

| Column | Data Type | Key / Constraint |
|---|---|---|
| job_id | INT | Primary Key, Auto Increment |
| recruiter_id | INT | Foreign Key, NOT NULL |
| title | VARCHAR(150) | NOT NULL |
| description | TEXT | NULL allowed |
| required_experience | DECIMAL(4,1) | NOT NULL, DEFAULT 0.0 |
| location | VARCHAR(150) | NULL allowed |
| posted_date | DATE | NOT NULL |
| expiry_date | DATE | NOT NULL |

Foreign key:
- `recruiter_id` references `recruiter(recruiter_id)`.
- ON DELETE RESTRICT.

Additional constraints:
- Required experience must be non-negative.
- Expiry date must not be earlier than posting date.
- Indexes: `recruiter_id`, `idx_job_expiry`, `idx_job_title`.

### 2.5 Skill

| Column | Data Type | Key / Constraint |
|---|---|---|
| skill_id | INT | Primary Key, Auto Increment |
| skill_name | VARCHAR(100) | UNIQUE, NOT NULL |

### 2.6 Candidate_Skill

| Column | Data Type | Key / Constraint |
|---|---|---|
| candidate_id | INT | Composite Primary Key, Foreign Key |
| skill_id | INT | Composite Primary Key, Foreign Key |

Foreign keys:
- `candidate_id` references `candidate(candidate_id)`.
- `skill_id` references `skill(skill_id)`.
- Both use ON DELETE CASCADE.

Composite primary key: `(candidate_id, skill_id)`.

### 2.7 Job_Skill

| Column | Data Type | Key / Constraint |
|---|---|---|
| job_id | INT | Composite Primary Key, Foreign Key |
| skill_id | INT | Composite Primary Key, Foreign Key |

Foreign keys:
- `job_id` references `job(job_id)`.
- `skill_id` references `skill(skill_id)`.
- Both use ON DELETE CASCADE.

Composite primary key: `(job_id, skill_id)`.

### 2.8 Application

| Column | Data Type | Key / Constraint |
|---|---|---|
| application_id | INT | Primary Key, Auto Increment |
| candidate_id | INT | Foreign Key, NOT NULL |
| job_id | INT | Foreign Key, NOT NULL |
| applied_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'Applied' |

Foreign keys:
- `candidate_id` references `candidate(candidate_id)`.
- `job_id` references `job(job_id)`.
- Both use ON DELETE RESTRICT.

Additional constraints:
- UNIQUE (`candidate_id`, `job_id`) prevents duplicate applications.
- Status must be one of: Applied, Under Review, Shortlisted, Rejected, Hired.
- Indexes: `job_id`, `idx_application_status`.

## 3. Entity Relationships

1. Company to Recruiter: One-to-Many.
2. Recruiter to Job: One-to-Many.
3. Candidate to Application: One-to-Many.
4. Job to Application: One-to-Many.
5. Candidate to Skill: Many-to-Many through Candidate_Skill.
6. Job to Skill: Many-to-Many through Job_Skill.

## 4. Normalization

### First Normal Form (1NF)

- Each table has a primary key.
- Every column contains atomic values.
- There are no repeating groups or multiple values stored in a single field.
- Candidate and job skills are stored separately using junction tables.

### Second Normal Form (2NF)

- The database satisfies 1NF.
- Every non-key attribute depends on the complete primary key.
- In Candidate_Skill and Job_Skill, the composite primary keys contain only the two foreign key columns, with no non-key attributes depending on part of the key.
- Other tables use single-column primary keys.

### Third Normal Form (3NF)

- The database satisfies 2NF.
- Non-key attributes depend on the key, the whole key, and nothing but the key.
- Company information is maintained separately from recruiter information.
- Recruiter information is maintained separately from job information.
- Skill details are stored in a separate Skill table.
- Junction tables resolve many-to-many relationships without storing redundant skill descriptions.
- Candidate and job details are not unnecessarily duplicated in the Application table.

Therefore, the relational schema is designed to satisfy 3NF based on its defined functional dependencies.

## 5. Database Objects

### View: candidate_job_match

Calculates the percentage of required job skills matched by each candidate.

Formula:

Match Percentage = (Matched Skills / Total Required Skills) × 100

The view considers jobs whose expiry date is greater than or equal to the current date.

Note: Jobs without entries in Job_Skill are excluded by the current view's inner join.

### Stored Procedure: Calculate_Match_Score

Accepts a candidate ID and job ID and returns:
- Candidate name.
- Job title.
- Experience details.
- Total required skills.
- Matched skills.
- Skill match percentage.
- Experience eligibility result.

### Trigger: Before_Application_Insert

Runs before an application is inserted.

It checks the job expiry date and prevents applications to expired jobs.

## 6. Integrity and Performance

The database uses:
- Primary keys to uniquely identify records.
- Foreign keys to maintain referential integrity.
- UNIQUE constraints to prevent duplicate email addresses, company names, and duplicate applications.
- CHECK constraints to validate experience, dates, and application status.
- Indexes to improve selected search and filtering operations.
- InnoDB for transactional and referential integrity support.

## 7. Conclusion

The TalentMatch database uses eight related tables, appropriate primary and foreign keys, junction tables, constraints, indexes, a view, a stored procedure, and a trigger.

Its normalized structure reduces unnecessary duplication and supports candidate-job matching and application management.
