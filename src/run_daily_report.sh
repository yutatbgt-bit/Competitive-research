#!/bin/bash
# run_daily_report.sh
# WSL内の cron などで毎日実行されるスクリプト

set -e

WORK_DIR="/home/yuta/project/store-tools/Competitive research"
cd "$WORK_DIR"

LOG_FILE="$WORK_DIR/auto_runner.log"

# ディレクトリの存在保証
mkdir -p "$WORK_DIR/report"

write_log() {
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "$timestamp - $1" >> "$LOG_FILE"
}

# 1. flockによる多重起動防止 (排他ロック)
LOCKFILE="$WORK_DIR/auto_runner.lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
    # 既に起動している場合は何もしない
    exit 0
fi

try_run() {
    write_log "Scheduled task started."

    local today
    today=$(date "+%Y-%m-%d")
    local last_success_file="$WORK_DIR/last_success.txt"

    # 2. 本日分のレポートがすでに作成されているかチェック
    if [ -f "$last_success_file" ]; then
        local last_success
        last_success=$(tr -d '[:space:]' < "$last_success_file")
        if [ "$last_success" = "$today" ]; then
            write_log "Today's report is already generated. Exiting."
            return 0
        fi
    fi

    # 3. ネットワーク接続を待機
    local check_urls=("https://www.google.com" "https://www.cloudflare.com" "https://www.amazon.com")
    local network_ready=false

    while [ "$network_ready" = false ]; do
        for ((i=0; i<60; i++)); do
            for url in "${check_urls[@]}"; do
                if curl -s -o /dev/null -I -w "%{http_code}" --connect-timeout 5 "$url" | grep -q "200"; then
                    network_ready=true
                    break
                fi
            done
            if [ "$network_ready" = true ]; then
                break
            fi
            sleep 10
        done

        if [ "$network_ready" = false ]; then
            write_log "Offline. Will check again in 10 minutes..."
            sleep 600
        fi
    done

    write_log "Online detected. Updating report (within_2km) via AI..."
    
    # パスを通す（uvコマンドがインストールされていると想定されるパスを追加）
    export PATH="$HOME/.local/bin:$PATH"

    if ! uv run src/update_report.py --mode within_2km >> "$LOG_FILE" 2>&1; then
        write_log "Error: update_report.py --mode within_2km failed. Exiting."
        return 1
    fi

    write_log "Updating report (no_limit) via AI..."
    if ! uv run src/update_report.py --mode no_limit >> "$LOG_FILE" 2>&1; then
        write_log "Error: update_report.py --mode no_limit failed. Exiting."
        return 1
    fi

    write_log "Running auto_lookup_competitors.py..."
    if ! uv run src/auto_lookup_competitors.py >> "$LOG_FILE" 2>&1; then
        write_log "Warning: auto_lookup_competitors.py failed. Continuing anyway."
    fi

    write_log "Running main.py (within_2km)..."
    if ! uv run src/main.py --mode within_2km >> "$LOG_FILE" 2>&1; then
        write_log "Error: uv run main.py --mode within_2km failed."
        return 1
    fi

    write_log "Running main.py (no_limit)..."
    if uv run src/main.py --mode no_limit >> "$LOG_FILE" 2>&1; then
        write_log "Report generated successfully. Committing to Git..."
        
        # Git操作
        git add data/stores_db.json last_success.txt report/
        git commit -m "chore: automatic daily report generation (2km & no limit)"
        
        write_log "Git commit completed. Exiting."
    else
        write_log "Error: uv run main.py --mode no_limit failed."
        return 1
    fi
}

# 実行およびエラーハンドリング
if ! try_run; then
    write_log "Task execution failed."
    exit 1
fi
