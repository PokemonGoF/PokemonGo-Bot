from yoyo import step

step(
    "CREATE TABLE evolve_log (pokemon text, iv real, cp real, dated datetime DEFAULT CURRENT_TIMESTAMP)"
)
