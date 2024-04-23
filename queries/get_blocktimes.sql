SELECT blockchain, time as block_timestamp, number as block_number FROM evms.blocks
WHERE blockchain = '{chain}' 
AND number >= {min_block}
AND number <= {max_block}