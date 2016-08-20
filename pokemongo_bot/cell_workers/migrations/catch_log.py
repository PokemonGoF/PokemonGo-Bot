from yoyo import step

step(
    "CREATE TABLE IF NOT EXISTS catch_log (pokemon text, cp real, iv real, encounter_id text, pokemon_id real, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
