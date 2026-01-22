-- Nettoyage préalable
DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

-- 1. Table Students (200 000 attendus)
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table Courses (1 000 attendus)
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    description TEXT,
    category VARCHAR(50)
);

-- 3. Table Enrollments (2 000 000 attendus)
CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(student_id),
    course_id INT REFERENCES courses(course_id),
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grade INT CHECK (grade BETWEEN 0 AND 100)
);

-- 4. Table Access Logs (5 000 000 attendus)
CREATE TABLE access_logs (
    log_id SERIAL PRIMARY KEY,
    student_id INT,
    url_accessed VARCHAR(255),
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INT
);
