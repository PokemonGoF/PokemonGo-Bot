from yoyo import step

step(
    "CREATE TABLE IF NOT EXISTS shadowban_log (username text, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
