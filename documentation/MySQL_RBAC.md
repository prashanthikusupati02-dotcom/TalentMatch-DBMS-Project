\# MySQL Database-Level Role-Based Access Control (RBAC)



\## 1. Overview



TalentMatch implements database-level Role-Based Access Control (RBAC) using MySQL 8.0 roles and dedicated database accounts.



Two roles are created:

\- `candidate\_role`

\- `recruiter\_role`



Each role receives permissions according to the responsibilities of the user.



\## 2. Roles and Permissions



\### Candidate Role



| Table | Permissions |

|---|---|

| job | SELECT |

| company | SELECT |

| skill | SELECT |

| job\_skill | SELECT |

| candidate\_job\_match | SELECT |

| candidate | SELECT, INSERT, UPDATE |

| candidate\_skill | SELECT, INSERT, DELETE |

| application | SELECT, INSERT |



\### Recruiter Role



| Table | Permissions |

|---|---|

| candidate | SELECT |

| candidate\_skill | SELECT |

| job | SELECT, INSERT, UPDATE, DELETE |

| job\_skill | SELECT, INSERT, UPDATE, DELETE |

| application | SELECT, UPDATE |

| company | SELECT |

| skill | SELECT |

| recruiter | SELECT |



\## 3. Database Accounts



Two dedicated MySQL accounts are configured:



\- `candidate\_db\_user` assigned to `candidate\_role`.

\- `recruiter\_db\_user` assigned to `recruiter\_role`.



Both roles are configured as their respective accounts' default roles.



\## 4. Security Testing



The following tests were performed successfully:



| Test | Expected Result | Actual Result |

|---|---|---|

| Recruiter views jobs | Allowed | Passed |

| Recruiter updates candidate | Denied | Passed |

| Candidate views jobs | Allowed | Passed |

| Candidate updates job | Denied | Passed |

| Recruiter default role activation | Active | Passed |

| Candidate default role activation | Active | Passed |



\### Example Permission Denial



Recruiter attempting to update a candidate:



```sql

UPDATE candidate

SET name = name

WHERE candidate\_id = -1;

```



Result:



```text

ERROR 1142 (42000):

UPDATE command denied for table 'candidate'

```



Candidate attempting to update a job:



```sql

UPDATE job

SET title = title

WHERE job\_id = -1;

```



Result:



```text

ERROR 1142 (42000):

UPDATE command denied for table 'job'

```



\## 5. Conclusion



MySQL database-level RBAC successfully restricts database operations according to user roles. Dedicated accounts, default role activation, and permission-denial tests demonstrate that unauthorized operations are blocked by the database itself.



\*\*Note:\*\* These are table-level permissions. Restricting candidates to their own individual records requires additional row-level authorization in the application or database.

