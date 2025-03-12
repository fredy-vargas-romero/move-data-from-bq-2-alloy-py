SELECT 
    id, 
    name, 
    email, 
    created_at 
FROM users 
WHERE id = :user_id
