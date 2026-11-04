```sql
USE job_matching_db;

DELIMITER //

CREATE PROCEDURE Calculate_Match_Score(
    IN p_candidate_id INT,
    IN p_job_id INT
)
BEGIN
    SELECT
        c.name AS candidate_name,
        j.title AS job_title,
        c.experience_years,
        j.required_experience,
        COUNT(js.skill_id) AS total_required_skills,
        COUNT(cs.skill_id) AS matched_skills,
        ROUND(
            COUNT(cs.skill_id) * 100.0 /
            NULLIF(COUNT(js.skill_id), 0),
            2
        ) AS skill_match_percentage,
        CASE
            WHEN c.experience_years >= j.required_experience
                THEN 'Experience Meets Requirement'
            ELSE 'More Experience Needed'
        END AS experience_result
    FROM Candidate c
    JOIN Job j ON j.job_id = p_job_id
    LEFT JOIN Job_Skill js ON js.job_id = j.job_id
    LEFT JOIN Candidate_Skill cs
        ON cs.candidate_id = c.candidate_id
        AND cs.skill_id = js.skill_id
    WHERE c.candidate_id = p_candidate_id
    GROUP BY
        c.candidate_id,
        c.name,
        j.job_id,
        j.title,
        c.experience_years,
        j.required_experience;
END //

CREATE TRIGGER Before_Application_Insert
BEFORE INSERT ON Application
FOR EACH ROW
BEGIN
    DECLARE job_expiry DATE;

    SELECT expiry_date
    INTO job_expiry
    FROM Job
    WHERE job_id = NEW.job_id;

    IF job_expiry < CURRENT_DATE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot apply: this job has expired.';
    END IF;
END //

DELIMITER ;
```
DELIMITER //

CREATE FUNCTION Get_Skill_Match_Percentage(
    p_candidate_id INT,
    p_job_id INT
)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_skills INT DEFAULT 0;
    DECLARE matched_skills INT DEFAULT 0;

    SELECT COUNT(*) INTO total_skills
    FROM Job_Skill
    WHERE job_id = p_job_id;

    SELECT COUNT(*) INTO matched_skills
    FROM Job_Skill js
    INNER JOIN Candidate_Skill cs
        ON js.skill_id = cs.skill_id
    WHERE js.job_id = p_job_id
      AND cs.candidate_id = p_candidate_id;

    IF total_skills = 0 THEN
        RETURN 0.00;
    END IF;

    RETURN ROUND(matched_skills * 100.0 / total_skills, 2);
END //

DELIMITER ;