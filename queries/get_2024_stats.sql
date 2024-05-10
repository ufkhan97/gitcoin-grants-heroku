SELECT
  SUM(r."total_amount_donated_in_usd") as crowdfunded_usd,
  SUM(CASE WHEN r."matching_distribution" IS NOT NULL THEN r."match_amount_in_usd" ELSE 0 END) AS matchingfunds,
  count(r."matching_distribution") as num_rounds,
  sum(r."total_donations_count") as num_donations
  
  --count(distinct r."donor_address") as unique_voters,
  --count(distinct r."recipient_address") as unique_grantees

FROM
  "chain_data_63"."rounds" AS r
WHERE 
  r."donations_end_time" >= '2024-01-01';
