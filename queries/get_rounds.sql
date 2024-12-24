WITH program_data AS (
    SELECT
        gg.round_number,
        gg.program,
        gg.type AS type,
        gg.chain_name AS chain_name,
        gg.chain_id AS chain_id,
        gg.round_id AS round_id
    FROM
        program_round_labels gg
    WHERE program IS NOT NULL
        AND LOWER("round_id") NOT IN ('0x911ae126be7d88155aa9254c91a49f4d85b83688', '0x40511f88b87b69496a3471cdbe1d3d25ac68e408', '0xc08008d47e3deb10b27fc1a75a96d97d11d58cf8', '0xb5c0939a9bb0c404b028d402493b86d9998af55e')
)
SELECT
    (r."round_metadata" #>> '{name}')::text AS "round_name",
    pd.round_number AS "round_number",
    pd.program AS "program",
    pd.type AS "type",
    pd.chain_name AS "chain_name",
    r."total_amount_donated_in_usd" AS "amountUSD",
    r."total_donations_count" AS "votes",
    r."unique_donors_count" AS "uniqueContributors",
    r."chain_id",
    LOWER(r."id") AS "round_id",
    "donations_end_time" AS "donations_end_time",
    "donations_start_time" AS "donations_start_time",
    (r."round_metadata" #>> '{quadraticFundingConfig, matchingCap}')::boolean AS "has_matching_cap",
    (r."round_metadata" #>> '{quadraticFundingConfig, matchingCapAmount}')::double precision AS "matching_cap_amount",
    (r."round_metadata" #>> '{quadraticFundingConfig, matchingFundsAvailable}')::double precision AS "matching_funds_available",
    r."match_amount_in_usd",
    r."match_token_address" AS "token",
    (r."round_metadata" #>> '{quadraticFundingConfig, minDonationThreshold}')::boolean AS "has_min_donation_threshold",
    (r."round_metadata" #>> '{quadraticFundingConfig, minDonationThresholdAmount}')::double precision AS "min_donation_threshold_amount",
    (r."round_metadata" #>> '{quadraticFundingConfig, sybilDefense}')::text AS "sybilDefense"
FROM
    public.rounds AS r
JOIN 
    program_data pd ON pd.round_id = r.id AND pd.chain_id = r.chain_id
WHERE
    r."chain_id" != 11155111 -- DO NOT USE SEPOLIA
    AND "donations_end_time" <= '2030-01-01'
    AND (r."round_metadata" #>> '{name}')::text IS NOT NULL
