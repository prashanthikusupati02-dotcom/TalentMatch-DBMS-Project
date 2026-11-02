USE job_matching_db;

CREATE OR REPLACE VIEW candidate_job_match AS
SELECT
    c.candidate_id AS candidate_id,
    c.name AS candidate_name,
    j.job_id AS job_id,
    j.title AS job_title,
    COUNT(js.skill_id) AS total_required_skills,
    COUNT(cs.skill_id) AS matched_skills,
    ROUND(
        (COUNT(cs.skill_id) * 100.0) /
        NULLIF(COUNT(js.skill_id), 0),
        2
    ) AS match_percentage
FROM
    (((candidate c
    JOIN job j)
    JOIN job_skill js
        ON js.job_id = j.job_id)
    LEFT JOIN candidate_skill cs
        ON cs.candidate_id = c.candidate_id
        AND cs.skill_id = js.skill_id)
WHERE
    j.expiry_date >= CURDATE()
GROUP BY
    c.candidate_id,
    c.name,
    j.job_id,
    j.title;