#!/bin/bash
# register_task.sh
# Windows タスクスケジューラに毎日AM5:00の自動実行タスクを登録するスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DISTRO="${WSL_DISTRO_NAME:-Ubuntu}"
TASK_NAME="IkariCompetitiveReportDailyRunner"
EXEC_TIME="05:00"

echo "=== Windows タスクスケジューラ 登録 ==="
echo "WSL ディストリビューション: $DISTRO"
echo "作業ディレクトリ:           $WORK_DIR"
echo "タスク名:                   $TASK_NAME"
echo "実行時刻:                   毎日 $EXEC_TIME"

# タスクのアクションコマンドを組み立て
COMMAND="wsl.exe -d $DISTRO bash -lic 'cd $WORK_DIR && bash src/run_daily_report.sh'"

# Windows の schtasks.exe を使ってタスクを登録
if /mnt/c/Windows/system32/schtasks.exe /create /tn "$TASK_NAME" /tr "$COMMAND" /sc daily /st "$EXEC_TIME" /f; then
    echo ""
    echo "[SUCCESS] タスクスケジューラに正常に登録されました！"
    echo "毎日 $EXEC_TIME に WSL バックグラウンドでレポート生成タスクが自動実行されます。"
else
    echo ""
    echo "[ERROR] タスクの登録に失敗しました。"
    exit 1
fi
