from yoyo import step

step(
    "CREATE TABLE transfer_log (pokemon text, iv real, cp real, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
