-- Run these examples against TaskManager/db.sqlite3 after migrations and seed_qa.

-- 1. Inspect tasks and their owners
SELECT t.id, t.title, t.priority, t.is_completed, u.username
FROM tasks_task t
JOIN auth_user u ON u.id = t.owner_id
ORDER BY t.id;

-- 2. Count tasks per user
SELECT u.username, COUNT(t.id) AS task_count
FROM auth_user u
LEFT JOIN tasks_task t ON t.owner_id = u.id
GROUP BY u.id, u.username
ORDER BY task_count DESC;

-- 3. Find incomplete High priority tasks
SELECT id, title, due_date
FROM tasks_task
WHERE priority = 'high' AND is_completed = 0
ORDER BY due_date;

-- 4. Verify the isolation fixture exists for qa_other
SELECT t.title, u.username
FROM tasks_task t
JOIN auth_user u ON u.id = t.owner_id
WHERE t.title = 'PRIVATE OTHER USER TASK';
