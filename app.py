import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --------------------------
# Database Connection
# --------------------------
engine = create_engine("postgresql+psycopg2://postgres:1234@localhost:5432/Exams")

# --------------------------
# Streamlit UI
# --------------------------
st.title("📊 Student Exam Dashboard")

# Step 1: Year Selection
years = pd.read_sql("SELECT DISTINCT year FROM recap ORDER BY year", engine)["year"].tolist()
selected_year = st.selectbox("Select Year", years)

# Step 2: Semester Selection
semesters = pd.read_sql(
    f"""
    SELECT DISTINCT semester 
    FROM recap 
    WHERE year = '{selected_year}' 
    ORDER BY semester
    """,
    engine
)["semester"].tolist()
selected_semester = st.selectbox("Select Semester", semesters)

# Step 3: Batch Selection
batches = pd.read_sql(
    f"""
    SELECT DISTINCT class 
    FROM recap 
    WHERE year = '{selected_year}' 
      AND semester = '{selected_semester}'
    ORDER BY class
    """,
    engine
)["class"].tolist()
selected_batch = st.selectbox("Select Batch", batches)

# Step 4: Course Selection
courses = pd.read_sql(
    f"""
    SELECT DISTINCT c.cid, c.title 
    FROM recap r 
    JOIN course c ON r.cid = c.cid
    WHERE r.year = '{selected_year}' 
      AND r.semester = '{selected_semester}'
      AND r.class = '{selected_batch}'
    """,
    engine
)
selected_course = st.selectbox("Select Course", courses["title"])
course_id = courses.loc[courses["title"] == selected_course, "cid"].values[0]

# Step 5: Show Failure Rate for Selected Course
query = f"""
WITH student_scores AS (
    SELECT 
        m.regno,
        r.cid,
        SUM(m.marks) AS Marks_Obtained,
        SUM(d.total) AS Total_Marks
    FROM marks m
    JOIN dist d ON m.hid = d.hid AND m.rid = d.rid
    JOIN recap r ON m.rid = r.rid
    WHERE r.year = '{selected_year}'
      AND r.semester = '{selected_semester}'
      AND r.class = '{selected_batch}'
      AND r.cid = '{course_id}'
    GROUP BY m.regno, r.cid
),
student_results AS (
    SELECT 
        s.regno,
        s.cid,
        s.Marks_Obtained,
        s.Total_Marks,
        CASE 
            WHEN s.Marks_Obtained < (0.55 * s.Total_Marks) THEN 1
            ELSE 0
        END AS is_fail
    FROM student_scores s
)
SELECT 
    st.name AS student_name,
    sr.regno,
    sr.Marks_Obtained,
    sr.Total_Marks,
    ROUND(((sr.Marks_Obtained::numeric / sr.Total_Marks::numeric) * 100)::numeric, 2) AS percentage,
    sr.is_fail
FROM student_results sr
JOIN student st ON sr.regno = st.regno
ORDER BY percentage ASC;
"""


# ✅ FIX: Use engine instead of conn
df = pd.read_sql(query, engine)

# Show Results
st.subheader("📌 Student Results")
st.dataframe(df)

# Failure rate metric
fail_rate = df["is_fail"].mean() * 100
st.metric("Failure Rate (%)", f"{fail_rate:.2f}%")
