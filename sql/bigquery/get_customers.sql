WITH ranked_customers AS (
  SELECT
    customer_id,
    name,
    email,
    signup_date,
    COALESCE(total_spent, 0.0) as total_spent,
    -- Use ROW_NUMBER to get the latest record per customer_id
    ROW_NUMBER() OVER (
      PARTITION BY customer_id 
      ORDER BY signup_date DESC, total_spent DESC
    ) as row_num
  FROM `nodal-cogency-451902-e0.my_dataset.customers`
)
SELECT
  customer_id,
  name,
  email,
  signup_date,
  total_spent
FROM ranked_customers
WHERE row_num = 1  -- Take only the first row for each customer_id
ORDER BY signup_date DESC
