SELECT
    count(*) as "num_donations",
    count(distinct donor_address) as unique_voters,
    count(distinct "recipient_address") as unique_grantees,
    sum("amount_in_usd") as "crowdfunded_usd",
    max(timestamp) as "last_donation",
    11700000 as "bounties_distributed",
    COUNT(DISTINCT "public"."all_donations"."donor_address" || ' ' || "public"."all_donations"."timestamp") as "transactions",
    (SELECT sum("match_amount_in_usd") FROM all_matching) as "matchingfunds",
    (SELECT count(distinct "round_id") as "num_rounds" FROM all_matching ) as "num_rounds",
    (SELECT sum("amount_in_usd") as USD FROM "public"."applications_payouts" WHERE chain_id != 11155111) as direct_grants_payouts,
    (SELECT SUM("amount_in_usd") AS "amount_in_usd" FROM "public"."AlloRoundsOutsideIndexer" WHERE timestamp <= CURRENT_TIMESTAMP) as other_gmv,
    (SELECT sum(voice_credit_balance)/ (100000) * 3000 as USD FROM maci."contributions" mc WHERE mc.timestamp >= '2024-01-01' AND "chain_id" != 11155111) as maci_crowdfunding
FROM
    all_donations
    
   
   