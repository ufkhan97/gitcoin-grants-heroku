SELECT
    round_num, 
    count(*) as "num_donations",
    count(distinct voter) as "unique_voters",
    count(distinct "payout_address") as "unique_grantees",
    sum("amount_usd") as "crowdfunded_usd",
    max(tx_timestamp) as "last_donation"
FROM
   all_donations 
GROUP BY
    round_num