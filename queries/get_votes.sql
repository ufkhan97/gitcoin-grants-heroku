SELECT
  (
    a."metadata" #>> array [ 'application',
    'project',
    'title' ] :: text [ ]
  ) :: text AS "project_name",
    d.id,
    d.chain_id,
    d.round_id,
    d.application_id,
    d.donor_address as "voter",
    d.recipient_address as "grantAddress",
    d.project_id as "projectId",
    d.transaction_hash,
    d.block_number as "blockNumber",
    d.token_address as "token",
    d.amount,
    d.amount_in_usd as "amountUSD",
    d.amount_in_round_match_token,
    d.timestamp as "block_timestamp"
FROM
    "chain_data_63".donations d
LEFT JOIN "chain_data_63".applications a ON a.round_id = d.round_id AND a.id = d.application_id
AND a.status = 'APPROVED'
WHERE d.round_id IN {round_id_list}
AND d.chain_id = '{chain_id}'
