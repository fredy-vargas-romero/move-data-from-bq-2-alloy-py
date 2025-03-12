SELECT 
    id,
    COALESCE(name, '') as name,
    COALESCE(email, '') as email,
    TIMESTAMP(created_at) as created_at,
    COALESCE(status, 'active') as status,
    TIMESTAMP(updated_at) as updated_at
FROM 
    `nodal-cogency-451902-e0.my_dataset.users`
WHERE 
    created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
