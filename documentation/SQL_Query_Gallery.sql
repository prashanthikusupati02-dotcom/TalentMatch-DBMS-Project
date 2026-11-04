
USE job_matching_db;

-- 1. Basic SELECT and WHERE
SELECT candidate_id, name, experience_years
FROM Candidate
WHERE experience_years >= 1
ORDER BY experience_years DESC;


-- 2. INNER JOIN: Jobs with recruiter and company details
SELECT
    j.job_id,
    j.title,
    r.name AS recruiter_name,
    c.company_name
FROM Job j
INNER JOIN Recruiter r ON j.recruiter_id = r.recruiter_id
INNER JOIN Company c ON r.company_id = c.company_id;


-- 3. GROUP BY and HAVING: Number of jobs posted by recruiters
SELECT
    recruiter_id,
    COUNT(*) AS total_jobs
FROM Job
GROUP BY recruiter_id
HAVING COUNT(*) >= 1;


-- 4. Nested subquery: Candidates with above-average experience
SELECT candidate_id, name, experience_years
FROM Candidate
WHERE experience_years >
    (SELECT AVG(experience_years) FROM Candidate);


-- 5. Correlated subquery: Candidates who have applied to a job
SELECT c.candidate_id, c.name
FROM Candidate c
WHERE EXISTS (
    SELECT 1
    FROM Application a
    WHERE a.candidate_id = c.candidate_id
);


-- 6. CTE: Count applications for each job
WITH JobApplicationCount AS (
    SELECT job_id, COUNT(*) AS total_applications
    FROM Application
    GROUP BY job_id
)
SELECT
    j.title,
    COALESCE(jac.total_applications, 0) AS total_applications
FROM Job j
LEFT JOIN JobApplicationCount jac
    ON j.job_id = jac.job_id;


-- 7. Recursive CTE: Generate numbers from 1 to 5
WITH RECURSIVE NumberSeries AS (
    SELECT 1 AS number
    UNION ALL
    SELECT number + 1
    FROM NumberSeries
    WHERE number < 5
)
SELECT number FROM NumberSeries;


-- 8. View: Candidate-job matching results
SELECT *
FROM candidate_job_match
ORDER BY match_percentage DESC;


-- 9. Stored procedure: Calculate candidate-job match score
CALL Calculate_Match_Score(1, 1);


-- 10. Transaction: Demonstrate application status update
START TRANSACTION;

UPDATE Application
SET status = 'Under Review'
WHERE application_id = 1;

SELECT * FROM Application
WHERE application_id = 1;

-- Use COMMIT to save the change.
-- Use ROLLBACK instead if you want to undo it.
ROLLBACK;


-- 11. Index inspection
SHOW INDEX FROM Candidate;
SHOW INDEX FROM Job;
SHOW INDEX FROM Application;


-- 12. Query execution plan
EXPLAIN
SELECT *
FROM Job
WHERE expiry_date >= CURRENT_DATE;
