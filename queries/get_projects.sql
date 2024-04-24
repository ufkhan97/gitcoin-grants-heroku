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
    "chain_data_63".applications AS a
WHERE 
    a.round_id IN {round_id_list} 
    AND a.chain_id = '{chain_id}' 
    AND a.status = 'APPROVED'
