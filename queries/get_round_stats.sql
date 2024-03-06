SELECT
    round_num, 
    count(*) as "num_donations",
    count(distinct voter) as "unique_voters",
    count(distinct "payoutaddress") as "unique_grantees",
    sum("amountUSD") as "crowdfunded_usd",
    max(tx_timestamp) as "last_donation"
FROM
   all_donations 
GROUP BY
    round_num