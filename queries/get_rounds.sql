SELECT
    (r."round_metadata" #>> '{name}')::text AS "round_name",
    r."total_amount_donated_in_usd" AS "amountUSD",
    r."total_donations_count" AS "votes",
    r."unique_donors_count" AS "uniqueContributors",
    r."chain_id",
    r."id" AS "round_id",
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
    "chain_data_75"."rounds" AS r
WHERE
    "chain_id" != 11155111 -- DO NOT USE SEPOLIA
    AND "donations_end_time" <= '2030-01-01'
    AND (r."round_metadata" #>> '{name}')::text IS NOT NULL
