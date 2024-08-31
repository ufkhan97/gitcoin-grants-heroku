SELECT
    d.round_num,
    count(*) as "num_donations",
    count(distinct d.donor_address) as "unique_voters",
    count(distinct d."recipient_address") as "unique_grantees",
    sum(d."amount_in_usd") as "crowdfunded_usd",
    max(d.timestamp) as "last_donation",
    coalesce(m.match_amount_in_usd, 0) as "matchingfunds"
FROM
    all_donations d
LEFT JOIN
    (SELECT round_num, sum(match_amount_in_usd) as match_amount_in_usd
     FROM all_matching
     GROUP BY round_num) m ON d.round_num = m.round_num
GROUP BY
    d.round_num, m.match_amount_in_usd
ORDER BY
    d.round_num;