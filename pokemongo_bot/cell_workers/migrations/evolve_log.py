from yoyo import step

step(
    "CREATE TABLE IF NOT EXISTS evolve_log (pokemon text, iv real, cp real, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
