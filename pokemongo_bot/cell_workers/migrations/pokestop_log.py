from yoyo import step

step(
    "CREATE TABLE IF NOT EXISTS  pokestop_log (pokestop text, exp real, items text, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
