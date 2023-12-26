WITH rounds as (
    SELECT "public"."Round"."id" AS "id",
        (
            "public"."Round"."metadata"#>>array ['name']::text []
        )::text AS "name",
        CASE
            WHEN "public"."Round"."roundId" = '0x8dce7A66e0C310f9f89E847DBa83B2344D589161' THEN 0
            ELSE "public"."Round"."amountUSD"
        END AS "amountUSD",
        "public"."Round"."votes" AS "votes",
        "public"."Round"."matchAmount" AS "matchAmount",
        "public"."Round"."matchAmountUSD" AS "matchAmountUSD",
        "public"."Round"."uniqueContributors" AS "uniqueContributors",
        TIMESTAMP 'epoch' + ("public"."Round"."roundStartTime") * INTERVAL '1 second' as "round_start_time",
        TIMESTAMP 'epoch' + ("public"."Round"."roundEndTime") * INTERVAL '1 second' as "round_end_time",
        "public"."Round"."chainId" AS "chainId",
        "public"."Round"."roundId" AS "roundId",
        (
            "public"."Round"."metadata"#>>ARRAY ['support', 'info']
        )::varchar AS "support_info",
        (
            "public"."Round"."metadata"#>>ARRAY ['support', 'type']
        )::varchar AS "support_type"
    FROM "public"."Round"
    WHERE "amountUSD" >= 10
        AND "votes" >= 10
        AND "matchAmountUSD" >= 10
        AND (
            TIMESTAMP 'epoch' + ("public"."Round"."roundEndTime") * INTERVAL '1 second'
        ) <= CURRENT_DATE
        AND ("public"."Round"."metadata"->>'name')::text NOT LIKE '%test%'
        AND ("public"."Round"."metadata"->>'name')::text NOT LIKE '%Test%'
),
summary as (
    SELECT count(distinct id) as num_rounds,
        sum(votes) as num_votes,
        sum("amountUSD") as crowdfunding,
        sum("matchAmountUSD") as matchingfunds
    FROM rounds
)
SELECT (s.num_rounds + 105) as num_rounds,
    (s.num_votes + 3720898) as num_votes,
    (s.crowdfunding + 34455859.80) as crowdfunding,
    (s.matchingfunds + 17501999.00) as matchingfunds,
    (
        s.crowdfunding + 34455859.80 + s.matchingfunds + 17501999.00
    ) as total_funding
FROM summary s