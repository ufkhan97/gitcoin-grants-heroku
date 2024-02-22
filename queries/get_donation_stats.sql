SELECT
    count(*) as "num_donations",
    count(distinct voter) as unique_voters,
    count(distinct "payout_address") as unique_grantees,
    sum("amount_usd") as "crowdfunded_usd",
    max(tx_timestamp) as "last_donation",
    11700000 as "bounties_distributed"
FROM
   all_donations 