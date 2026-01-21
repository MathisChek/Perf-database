-- 1. Générer 200 000 étudiants
INSERT INTO students (first_name, last_name, email, registration_date)
SELECT
    'Student' || i,
    'Name' || i,
    'student' || i || '@elearning.com',
    NOW() - (random() * interval '365 days')
FROM generate_series(1, 200000) AS i;

-- 2. Générer 1 000 cours
INSERT INTO courses (title, description, category)
SELECT
    'Course ' || i,
    'Description for course ' || i,
    CASE (i % 5)
        WHEN 0 THEN 'Math'
        WHEN 1 THEN 'Science'
        WHEN 2 THEN 'History'
        WHEN 3 THEN 'IT'
        ELSE 'Art'
    END
FROM generate_series(1, 1000) AS i;

-- 3. Générer 2 000 000 inscriptions
-- On associe aléatoirement des étudiants (1-200000) à des cours (1-1000)
INSERT INTO enrollments (student_id, course_id, enrollment_date, grade)
SELECT
    (random() * 199999 + 1)::INT, -- Random student_id
    (random() * 999 + 1)::INT,    -- Random course_id
    NOW() - (random() * interval '365 days'),
    (random() * 100)::INT
FROM generate_series(1, 2000000);

-- 4. Générer 5 000 000 de logs
INSERT INTO access_logs (student_id, url_accessed, access_time, duration_ms)
SELECT
    (random() * 199999 + 1)::INT,
    '/course/' || (random() * 999 + 1)::INT || '/module/' || (random() * 10)::INT,
    NOW() - (random() * interval '30 days'),
    (random() * 500 + 20)::INT -- Durée entre 20ms et 520ms
FROM generate_series(1, 5000000);
