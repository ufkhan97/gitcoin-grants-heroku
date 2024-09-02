WITH donation_stats AS (
    SELECT
        count(*) as num_donations,
        count(distinct donor_address) as unique_voters,
        count(distinct "recipient_address") as unique_grantees,
        sum("amount_in_usd") as crowdfunded_usd,
        max(timestamp) as last_donation,
        COUNT(DISTINCT donor_address || ' ' || timestamp) as transactions
    FROM all_donations
),
matching_stats AS (
    SELECT
        sum("match_amount_in_usd") as matchingfunds,
        count(distinct "round_id") as num_rounds
    FROM all_matching
),
direct_grants AS (
    SELECT sum("amount_in_usd") as direct_grants_payouts
    FROM "public"."applications_payouts"
    WHERE chain_id != 11155111
),
allo_rounds AS (
    SELECT SUM("amount_in_usd") AS other_gmv
    FROM "public"."AlloRoundsOutsideIndexer"
    WHERE timestamp <= CURRENT_TIMESTAMP
),
maci_contributions AS (
    SELECT sum(voice_credit_balance) / (100000) * 3000 as maci_crowdfunding
    FROM maci."contributions" mc
    WHERE mc.timestamp >= '2024-01-01' AND "chain_id" != 11155111
)
SELECT
    d.num_donations,
    d.unique_voters,
    d.unique_grantees,
    d.crowdfunded_usd,
    d.last_donation,
    11700000 as bounties_distributed,
    d.transactions,
    m.matchingfunds,
    m.num_rounds,
    dg.direct_grants_payouts,
    ar.other_gmv,
    mc.maci_crowdfunding
FROM donation_stats d
CROSS JOIN matching_stats m
CROSS JOIN direct_grants dg
CROSS JOIN allo_rounds ar
CROSS JOIN maci_contributions mc