#!/bin/bash
# unregister_task.sh
# Windows タスクスケジューラから自動実行タスクを削除するスクリプト

TASK_NAME="IkariCompetitiveReportDailyRunner"

echo "=== Windows タスクスケジューラ 登録解除 ==="
echo "タスク名: $TASK_NAME"

if /mnt/c/Windows/system32/schtasks.exe /delete /tn "$TASK_NAME" /f; then
    echo ""
    echo "[SUCCESS] タスク '$TASK_NAME' は正常に削除されました。"
else
    echo ""
    echo "[INFO] タスク '$TASK_NAME' は存在しないか、既に削除されています。"
fi
