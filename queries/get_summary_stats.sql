SELECT
    count(*) as "num_donations",
    count(distinct voter) as unique_voters,
    count(distinct "payoutaddress") as unique_grantees,
    sum("amountUSD") as "crowdfunded_usd",
    max(tx_timestamp) as "last_donation",
    11700000 as "bounties_distributed",
    COUNT(DISTINCT "public"."all_donations"."voter" || ' ' || "public"."all_donations"."tx_timestamp") as "transactions",
    (SELECT sum(match_amount_usd) FROM all_matching) as "matchingfunds",
    (SELECT count(distinct sub_round_slug) as "num_rounds" FROM all_matching ) as "num_rounds"
FROM
    all_donations
