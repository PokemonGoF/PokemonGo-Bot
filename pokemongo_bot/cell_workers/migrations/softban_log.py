from yoyo import step

step(
    "CREATE TABLE IF NOT EXISTS softban_log (status text, source text, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
