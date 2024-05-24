SELECT blockchain,
    min(number) as min_blocknumber,
    min(time) as min_block_timestamp,
    max(number) as max_blocknumber,
    max(time) as max_block_timestamp
FROM evms.blocks
WHERE blockchain = '{chain}'
    AND number >= {min_block}
    AND number <= {max_block}
GROUP BY blockchain