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
        sum("match_amount_in_usd") + 1250000 as matchingfunds,
        count(distinct "round_id") + 15 as num_rounds
    FROM all_matching
),
direct_grants AS (
    SELECT sum("amount_in_usd") as direct_grants_payouts,
    count(distinct concat(chain_id, '-', round_id)) as num_rounds
    FROM "public"."applications_payouts"
    WHERE chain_id != 11155111
),
allo_rounds AS (
    SELECT 
        SUM("amount_in_usd") AS other_gmv,
        count(*) AS num_rounds
    FROM "public"."AlloRoundsOutsideIndexer"
    WHERE timestamp <= CURRENT_TIMESTAMP
),
maci_contributions AS (
    SELECT sum(voice_credit_balance) / (100000) * 3000 as maci_crowdfunding,
    count(distinct concat(chain_id, '-', round_id)) as num_rounds
    FROM maci."contributions" mc
    WHERE mc.timestamp >= '2024-01-01' AND "chain_id" != 11155111
),
combined_stats AS (
    SELECT
        d.num_donations,
        d.unique_voters,
        d.unique_grantees,
        d.crowdfunded_usd,
        d.last_donation,
        11700000 as bounties_distributed,
        d.transactions,
        m.matchingfunds,
        m.num_rounds as matching_rounds,
        dg.direct_grants_payouts,
        dg.num_rounds as direct_grant_rounds,
        ar.other_gmv,
        ar.num_rounds as allo_rounds,
        mc.maci_crowdfunding,
        mc.num_rounds as maci_rounds,
        (d.crowdfunded_usd + m.matchingfunds + 11700000 + dg.direct_grants_payouts + ar.other_gmv + mc.maci_crowdfunding) as total_usd,
        (m.num_rounds + dg.num_rounds + ar.num_rounds + mc.num_rounds) as total_rounds
    FROM donation_stats d
    CROSS JOIN matching_stats m
    CROSS JOIN direct_grants dg
    CROSS JOIN allo_rounds ar
    CROSS JOIN maci_contributions mc
)
SELECT 
    total_usd,
    total_rounds,
    unique_grantees as total_grantees,
    num_donations
FROM combined_stats