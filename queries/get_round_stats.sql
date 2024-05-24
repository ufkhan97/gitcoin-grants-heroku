SELECT
    d.round_num,
    count(*) as "num_donations",
    count(distinct d.voter) as "unique_voters",
    count(distinct d."payoutaddress") as "unique_grantees",
    sum(d."amountUSD") as "crowdfunded_usd",
    max(d.tx_timestamp) as "last_donation",
    coalesce(m.match_amount_usd, 0) as "matchingfunds"
FROM
    all_donations d
LEFT JOIN
    (SELECT round_num, sum(match_amount_usd) as match_amount_usd
     FROM all_matching
     GROUP BY round_num) m ON d.round_num = m.round_num
GROUP BY
    d.round_num, m.match_amount_usd
ORDER BY
    d.round_num;