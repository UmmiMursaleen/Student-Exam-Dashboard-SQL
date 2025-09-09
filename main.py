import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------------
# Database Connection
# -------------------------------
engine = create_engine("postgresql+psycopg2://postgres:1234@localhost:5432/Exams")

st.title("📊 Student Exam Dashboard")

# -------------------------------
# Step 1: Year Selection
# -------------------------------
query_years = text("SELECT DISTINCT year FROM recap ORDER BY year")
years = pd.read_sql(query_years, engine)["year"].tolist()
selected_year = st.selectbox("Select Year", years)

# -------------------------------
# Step 2: Semester Selection
# -------------------------------
query_semesters = text("""
    SELECT DISTINCT semester 
    FROM recap 
    WHERE year = :year 
    ORDER BY semester
""")
semesters = pd.read_sql(query_semesters, engine, params={"year": selected_year})["semester"].tolist()
selected_semester = st.selectbox("Select Semester", semesters)

# -------------------------------
# Step 3: Batch Selection
# -------------------------------
query_batches = text("""
    SELECT DISTINCT class 
    FROM recap 
    WHERE year = :year 
      AND semester = :semester
    ORDER BY class
""")
batches = pd.read_sql(
    query_batches, engine, 
    params={"year": selected_year, "semester": selected_semester}
)["class"].tolist()
selected_batch = st.selectbox("Select Batch", batches)

# -------------------------------
# Step 4: Course Selection
# -------------------------------
query_courses = text("""
    SELECT DISTINCT c.cid, c.title 
    FROM recap r 
    JOIN course c ON r.cid = c.cid
    WHERE r.year = :year 
      AND r.semester = :semester
      AND r.class = :batch
""")
courses = pd.read_sql(
    query_courses, engine, 
    params={"year": selected_year, "semester": selected_semester, "batch": selected_batch}
)
selected_course = st.selectbox("Select Course", courses["title"])
course_id = int(courses.loc[courses["title"] == selected_course, "cid"].values[0])  # FIX: cast to int


# -------------------------------
# Step 5: Student Results + Failure Rate
# -------------------------------
query_results = text("""
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

""")

df = pd.read_sql(
    query_results, engine,
    params={
        "year": selected_year, 
        "semester": selected_semester, 
        "batch": selected_batch, 
        "course_id": course_id
    }
)

# -------------------------------
# Display Results
# -------------------------------
st.subheader("📌 Student Results")

if not df.empty:
    st.dataframe(df)

    # Failure Rate
    fail_rate = df["is_fail"].mean() * 100
    st.metric("Failure Rate (%)", f"{fail_rate:.2f}%")
else:
    st.warning("⚠️ No records found for the selected filters.")
    st.metric("Failure Rate (%)", "0.00%")
