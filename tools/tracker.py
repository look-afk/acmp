import os
import sys
import datetime
import pathlib
from collections import defaultdict

# Windows UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# Импортируем синхронизатор и логику из app.py
from app import get_stats_data

def run_cli():
    print("=" * 65)
    print("  🚀 ACMP TRACKER — ТОЧНАЯ СТАТИСТИКА (ТОЛЬКО ACCEPTED)")
    print("=" * 65)
    d = get_stats_data()
    print(f"\n📅 Дата: {d['today_str']}")
    sync = d.get("sync") or {}
    print(f"🌐 Синк ACMP: {'OK' if sync.get('ok') else 'ОШИБКА'} {sync.get('at','')} {sync.get('error','')}")
    print(f"✨ Задач курса C++ сдано сегодня (Accepted): \033[92m{d['today_count']}\033[0m")
    print(f"⚪ Задач сдано вчера: {d['yesterday_count']}")
    print(f"⚪ Задач сдано позавчера: {d['day_before_count']}")
    print(f"🏆 Прогресс курса: {d['course']['solved_tasks']}/{d['course']['total_tasks']} ({d['course']['percent']}%)")
    print(f"🔥 Текущий стрик: \033[93m{d['streak']} дн.\033[0m")
    
    if d["today_breakdown"]:
        print("\n📝 Сданные задачи за сегодня:")
        for item in d["today_breakdown"]:
            print(f"  • {item['category']}: {', '.join(item['tasks'])}")
    else:
        print("\n📝 За сегодня еще нет сданных задач на Accepted.")
    print("=" * 65)

if __name__ == "__main__":
    run_cli()
