#!/bin/bash
# launchd'nin çağırdığı sarmalayıcı. Kullanım: run.sh [aksam|sabah|test|gun YYYY-MM-DD [YYYY-MM-DD]]
# Mod verilmezse saate bakar: 18:00 sonrası aksam, öncesi sabah.
set -u
DIR="$HOME/.claude/timelog-gunluk"
mkdir -p "$DIR/logs"
cd "$DIR" || exit 1

MODE="${1:-}"
if [ -z "$MODE" ]; then
  if [ "$(date +%H)" -ge 18 ]; then MODE=aksam; else MODE=sabah; fi
else
  shift
fi
ARGS="$MODE ${*:-}"

# API anahtarı tanımlıysa claude.ai bağlantıları (Slack, Gmail, Takvim) kapanır.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN CLAUDECODE CLAUDE_CODE_ENTRYPOINT
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

TOOLS="Read,Write,Edit,Glob,Grep,ToolSearch,Bash(git -C:*),Bash(git log:*),Bash(ls:*),Bash(find:*),Bash(date:*)"
TOOLS="$TOOLS,mcp__timelog__get_me,mcp__timelog__list_timesheets,mcp__timelog__log_time,mcp__timelog__search_projects,mcp__timelog__list_activities"
TOOLS="$TOOLS,mcp__claude_ai_Slack__slack_send_message,mcp__claude_ai_Slack__slack_read_thread,mcp__claude_ai_Slack__slack_read_channel,mcp__claude_ai_Slack__slack_read_user_profile"
TOOLS="$TOOLS,mcp__claude_ai_Gmail__search_threads,mcp__claude_ai_Gmail__get_thread"
TOOLS="$TOOLS,mcp__claude_ai_Google_Calendar__list_events,mcp__claude_ai_Google_Calendar__list_calendars"

LOG="$DIR/logs/$(date +%Y-%m-%d-%H%M)-$MODE.log"
# Geliştirme: TIMELOG_GUNLUK_PLUGIN_DIR verilirse plugin oradan yüklenir.
EXTRA=()
[ -n "${TIMELOG_GUNLUK_PLUGIN_DIR:-}" ] && EXTRA=(--plugin-dir "$TIMELOG_GUNLUK_PLUGIN_DIR")
# Gece onay veren olmadığı için repo kökleri ve kurallar dosyasının klasörü baştan izinli olmalı.
i=0
while root=$(plutil -extract "repo_roots.$i" raw config.json 2>/dev/null); do
  EXTRA+=(--add-dir "${root/#\~/$HOME}"); i=$((i+1))
done
if rules=$(plutil -extract rules_file raw config.json 2>/dev/null); then
  rules="${rules/#\~/$HOME}"
  [ -L "$rules" ] && rules="$(cd "$(dirname "$rules")" && cd "$(dirname "$(readlink "$rules")")" && pwd)/x"
  EXTRA+=(--add-dir "$(dirname "$rules")")
fi
claude ${EXTRA[@]+"${EXTRA[@]}"} -p "/timelog-gunluk:gunluk $ARGS" --allowedTools "$TOOLS" --output-format text < /dev/null > "$LOG" 2>&1
echo "exit=$?" >> "$LOG"
# 30 günden eski logları sil
find "$DIR/logs" -name '*.log' -mtime +30 -delete 2>/dev/null
