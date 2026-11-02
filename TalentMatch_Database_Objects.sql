USE job_matching_db;

SHOW CREATE TABLE Company;
SHOW CREATE TABLE Recruiter;
SHOW CREATE TABLE Candidate;
SHOW CREATE TABLE Job;
SHOW CREATE TABLE Skill;
SHOW CREATE TABLE Candidate_Skill;
SHOW CREATE TABLE Job_Skill;
SHOW CREATE TABLE Application;

SHOW CREATE VIEW candidate_job_match;

SHOW CREATE PROCEDURE Calculate_Match_Score;

SHOW CREATE TRIGGER Before_Application_Insert;