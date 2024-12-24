WITH round_chain_pairs AS (
    SELECT unnest(ARRAY[%s]::text[]) AS round_id,
           unnest(ARRAY[%s]::text[]) AS chain_id
)
SELECT 
    a.id,
    (a.metadata->'application'->'project'->>'title') AS title,
    (a.metadata->'application'->>'recipient') AS recipient_address,
    (r."round_metadata" #>> '{name}')::text AS "round_name",
    a.chain_id,
    a.round_id,
    a.project_id AS "projectId",
    a.status,
    a.total_donations_count AS votes,
    a.total_amount_donated_in_usd AS "amountUSD",
    a.unique_donors_count
FROM 
    public.applications AS a
LEFT JOIN round r ON a.round_id = r.id AND a.chain_id = r.chain_id
JOIN round_chain_pairs rcp ON a.round_id = rcp.round_id AND a.chain_id = rcp.chain_id
WHERE 
    a.status = 'APPROVED';
