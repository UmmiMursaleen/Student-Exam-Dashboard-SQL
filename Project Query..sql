-- Get all the table and their columns and their datatype.

SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;




--  Step 1: Get Semesters for a Selected Year 
SELECT DISTINCT semester
FROM recap
WHERE year = :year;

-- Step 2: Get Batches for Year + Semester
SELECT DISTINCT class
FROM recap
WHERE year = :year 
  AND semester =:semester;
  
-- Step 3: Get Courses for Year + Semester + Batch
SELECT DISTINCT c.cid, c.title
FROM recap r
JOIN course c ON r.cid = c.cid
WHERE r.year = :year
  AND r.semester = :semester
  AND r.class = :batch;




-- Step 4: Failure Rate for Students in a Selected Course
WITH student_scores AS (
    SELECT 
        m.regno,
        r.cid,
        SUM(m.marks) AS Marks_Obtained,
        SUM(d.total) AS Total_Marks
    FROM marks m
    JOIN dist d ON m.hid = d.hid AND m.rid = d.rid
    JOIN recap r ON m.rid = r.rid
    WHERE r.year = :year
      AND r.semester = :semester
      AND r.class = :batch
      AND r.cid = :course_id
    GROUP BY m.regno, r.cid
),
student_results AS (
    SELECT 
        s.regno,
        s.cid,
        s.Marks_Obtained,
        s.Total_Marks,
        CASE 
            WHEN s.Marks_Obtained < 60 THEN 1
            ELSE 0
        END AS is_fail,
        g.grade
    FROM student_scores s
    JOIN grade g ON s.Marks_Obtained BETWEEN g.start AND g."end"
)
SELECT 
    st.name AS student_name,
    sr.regno,
    sr.Marks_Obtained,
    sr.Total_Marks,
    ROUND(((sr.Marks_Obtained::numeric / sr.Total_Marks::numeric) * 100)::numeric, 2) AS percentage,
    sr.is_fail,
    sr.grade
FROM student_results sr
JOIN student st ON sr.regno = st.regno
ORDER BY percentage ASC;
