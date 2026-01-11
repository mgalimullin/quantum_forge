#!/bin/bash

# ====== НАСТРОЙКИ ======
PROJECT_DIR="/Users/m.galimullin/workspace/practicum/07_sprint/quantum_forge/Task4"
PYTHON_BIN="$PROJECT_DIR/.venv-3.13/bin/python"
LOADER_SCRIPT="$PROJECT_DIR/loader.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/faiss_update.log"

# Cron: каждый день в 03:00
CRON_SCHEDULE="0 3 * * *"

# ====== ПОДГОТОВКА ======
mkdir -p "$LOG_DIR"

# Строка cron
CRON_JOB="$CRON_SCHEDULE cd $PROJECT_DIR && $PYTHON_BIN $LOADER_SCRIPT >> $LOG_FILE 2>&1"

# Проверяем, нет ли уже такой задачи
(crontab -l 2>/dev/null | grep -v "$LOADER_SCRIPT"; echo "$CRON_JOB") | crontab -

echo "✅ Cron-задача добавлена:"
echo "$CRON_JOB"
