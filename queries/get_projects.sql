SELECT 
    a.id,
    (a.metadata->'application'->'project'->>'title') AS title,
    (a.metadata->'application'->>'recipient') AS recipient_address,
    a.chain_id,
    a.round_id,
    a.project_id AS "projectId",
    a.status,
    a.total_donations_count AS votes,
    a.total_amount_donated_in_usd AS "amountUSD",
    a.unique_donors_count
FROM 
    public.applications AS a
WHERE 
    a.round_id = %(round_id)s 
    AND a.chain_id = '%(chain_id)s'
    AND a.status = 'APPROVED'
