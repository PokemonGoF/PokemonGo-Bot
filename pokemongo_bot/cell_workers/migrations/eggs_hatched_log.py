from yoyo import step

step(
    "CREATE TABLE IF NOT EXISTS eggs_hatched_log (pokemon text, cp real, iv real, pokemon_id real, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
