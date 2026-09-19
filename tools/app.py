import os
import sys
import re
import ssl
import json
import time
import datetime
import pathlib
import threading
import urllib.request
import urllib.parse
import http.cookiejar
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

# Windows UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

# ROOT_DIR указывает на корень проекта ACMP
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
ACMP_USER_ID = "32756"
ACMP_LOGIN = "Look__"
ACMP_PASSWORD = "[REDACTED]"

COURSE_STRUCTURE = {
    "Введение": {
        "Арифметика": {"total": 6, "topic_id": 26, "sec_id": 1},
        "Простые задачи": {"total": 8, "topic_id": 395, "sec_id": 1},
        "Целые числа": {"total": 9, "topic_id": 27, "sec_id": 1},
        "Вывод формул": {"total": 6, "topic_id": 28, "sec_id": 1},
    },
    "Условный оператор": {
        "Простые сравнения": {"total": 10, "topic_id": 29, "sec_id": 2},
        "Шахматы": {"total": 10, "topic_id": 30, "sec_id": 2},
        "Алгебра и геометрия": {"total": 9, "topic_id": 31, "sec_id": 2},
        "Сложные задачи": {"total": 4, "topic_id": 32, "sec_id": 2},
    },
    "Операторы цикла": {
        "Цикл с параметром (for)": {"total": 10, "topic_id": 33, "sec_id": 3},
        "Цикл с предусловием (while)": {"total": 9, "topic_id": 34, "sec_id": 3},
        "Цикл с постусловием (do ... while)": {"total": 14, "topic_id": 35, "sec_id": 3},
        "НОД и НОК": {"total": 4, "topic_id": 36, "sec_id": 3},
        "Бинарный поиск": {"total": 13, "topic_id": 37, "sec_id": 3},
    },
    "Строковые типы данных": {
        "Символьный тип (char)": {"total": 14, "topic_id": 38, "sec_id": 4},
        "Строковый тип (string)": {"total": 9, "topic_id": 39, "sec_id": 4},
        "Системы счисления": {"total": 12, "topic_id": 40, "sec_id": 4},
    },
    "Массивы": {
        "Линейный поиск": {"total": 6, "topic_id": 113, "sec_id": 5},
        "Преобразования и анализ данных": {"total": 10, "topic_id": 114, "sec_id": 5},
        "Массивы структур": {"total": 3, "topic_id": 115, "sec_id": 5},
    },
    "Функции": {
        "Функции - 1": {"total": 6, "topic_id": 116, "sec_id": 6},
        "Функции - 2": {"total": 6, "topic_id": 117, "sec_id": 6},
    },
    "Сортировка": {
        "Квадратичная сортировка": {"total": 9, "topic_id": 118, "sec_id": 7},
        "Быстрая сортировка": {"total": 4, "topic_id": 119, "sec_id": 7},
        "Сортировка структур": {"total": 3, "topic_id": 126, "sec_id": 7},
    },
    "Двумерные массивы": {
        "Базовые операции": {"total": 8, "topic_id": 120, "sec_id": 8},
        "Символьные матрицы": {"total": 6, "topic_id": 121, "sec_id": 8},
        "Целочисленные матрицы": {"total": 11, "topic_id": 122, "sec_id": 8},
    },
    "Рекурсия": {
        "Рекурсия - 1": {"total": 9, "topic_id": 123, "sec_id": 9},
        "Рекурсия - 2": {"total": 11, "topic_id": 124, "sec_id": 9},
    }
}

IGNORED_NAMES = {
    "manage.py", "tracker.py", "app.py", "Fill.py", "refill.py", "backup.py",
    "test_acmp_sync.py", "test_run.py", "Запустить_Трекер.bat", "main.py", "f1.py"
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CACHE_TTL_SEC = 180
SYNC_LOG = pathlib.Path(__file__).parent / "sync.log"
MIN_PARSED_PROBLEMS = 80

cached_acmp_data = {
    "accepted": set(),
    "accepted_dates": {},
    "topic_totals": {},
    "sync_ok": False,
    "logged_in": False,
    "sync_error": "Ещё не синхронизировано",
    "synced_at": "",
}
last_sync_time = 0
sync_lock = threading.Lock()


def log_sync(message):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {message}"
    print(f"[ACMP] {message}")
    try:
        with SYNC_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def make_opener(cj=None):
    if cj is None:
        cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=get_ssl_context())
    )
    return opener, cj


def clone_cookiejar(src):
    dst = http.cookiejar.CookieJar()
    for cookie in src:
        dst.set_cookie(cookie)
    return dst


def http_get(opener, url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=timeout) as resp:
        return resp.read().decode("windows-1251", errors="ignore")


def is_logged_in(html):
    low = html.lower()
    return (
        "main=exit" in low
        or "main=logout" in low
        or f"id={ACMP_USER_ID}" in low
        or f">{ACMP_LOGIN.lower()}<" in low
    )


def login_acmp():
    opener, cj = make_opener()
    login_data = urllib.parse.urlencode(
        {"lgn": ACMP_LOGIN, "password": ACMP_PASSWORD}
    ).encode("windows-1251")
    login_urls = (
        "https://acmp.ru/index.asp?main=enter",
        "https://acmp.ru/index.asp?main=login",
    )
    last_html = ""
    for url in login_urls:
        try:
            req = urllib.request.Request(
                url, data=login_data, headers={"User-Agent": USER_AGENT}
            )
            opener.open(req, timeout=12)
            last_html = http_get(opener, "https://acmp.ru/index.asp")
            if is_logged_in(last_html):
                return opener, cj, True
        except Exception as exc:
            log_sync(f"Ошибка входа через {url}: {exc}")
    return opener, cj, is_logged_in(last_html)


def parse_status_rows(html):
    rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.IGNORECASE | re.DOTALL)
    for row in rows:
        if "Accepted" not in row:
            continue
        date_match = re.search(
            r"(\d{2}\.\d{2}\.\d{4})\s+\d{1,2}:\d{2}:\d{2}",
            row,
        )
        problem_match = re.search(r"id_problem=(\d+)", row, re.IGNORECASE)
        if not date_match or not problem_match:
            continue
        try:
            accepted_date = datetime.datetime.strptime(date_match.group(1), "%d.%m.%Y").date()
        except ValueError:
            continue
        yield int(problem_match.group(1)), accepted_date


PROBLEM_LINK_RE = re.compile(
    r"(<b\b[^>]*>\s*)?(?:&nbsp;)?\s*<a\s+[^>]*id_problem=(\d+)[^>]*>\s*([A-Z])\.\s*[^<]*</a>",
    re.IGNORECASE,
)


def fetch_topic(opener, sec_name, top_name, top_info):
    """Fetch a topic page; Accepted = problem letter wrapped in <b> on ACMP."""
    top_id = top_info["topic_id"]
    sec_id = top_info["sec_id"]
    url = (
        f"https://acmp.ru/asp/do/index.asp?main=topic"
        f"&id_course=1&id_section={sec_id}&id_topic={top_id}"
    )
    html = http_get(opener, url, timeout=12)
    local_acc = set()
    local_p2t = {}
    letters = []
    # Буква может встретиться в тексте урока и в списке задач.
    # Accepted — если хотя бы одна ссылка этой буквы обёрнута в <b>.
    found = {}
    for match in PROBLEM_LINK_RE.finditer(html):
        problem_id = int(match.group(2))
        let = match.group(3).upper()
        is_accepted = bool(match.group(1))
        prev = found.get(let)
        found[let] = (problem_id, (prev[1] if prev else False) or is_accepted)
    for let, (problem_id, is_accepted) in found.items():
        letters.append(let)
        task_key = (sec_name, top_name, let)
        local_p2t[problem_id] = task_key
        if is_accepted:
            local_acc.add(task_key)
    if not local_p2t:
        raise RuntimeError(f"На странице темы нет задач: {sec_name} / {top_name}")
    return local_acc, local_p2t, letters


def fetch_accepted_submission_dates(cookiejar, problem_to_task):
    """Accepted dates for C++ course tasks only (id_course=1 mapped problems)."""
    import concurrent.futures as _cf
    dates = {}
    url_base = (
        f"https://acmp.ru/index.asp?main=status"
        f"&id_mem={ACMP_USER_ID}&id_res=1&id_t=0"
    )

    def fetch_page(page):
        opener, _ = make_opener(clone_cookiejar(cookiejar))
        url = url_base if page == 0 else f"{url_base}&page={page}"
        try:
            return http_get(opener, url, timeout=12)
        except Exception:
            return ""

    html0 = fetch_page(0)
    max_page = 0
    if html0:
        nums = [
            int(p)
            for p in re.findall(
                r"id_res=1[^\"'\s<>]*page=(\d+)",
                html0,
                re.IGNORECASE,
            )
        ]
        max_page = min(max(nums, default=0), 40)

    pages_html = {0: html0}
    if max_page > 0:
        with _cf.ThreadPoolExecutor(max_workers=6) as ex:
            future_map = {ex.submit(fetch_page, p): p for p in range(1, max_page + 1)}
            for fut in _cf.as_completed(future_map):
                pages_html[future_map[fut]] = fut.result()

    for html in pages_html.values():
        for problem_id, accepted_date in parse_status_rows(html):
            task_key = problem_to_task.get(problem_id)
            if not task_key:
                continue
            if task_key not in dates or accepted_date < dates[task_key]:
                dates[task_key] = accepted_date
    return dates


def sync_acmp_status(force=False):
    global last_sync_time, cached_acmp_data
    import concurrent.futures as _cf

    with sync_lock:
        now = time.time()
        if not force and last_sync_time and now - last_sync_time < CACHE_TTL_SEC:
            return cached_acmp_data

        try:
            opener, cookiejar, logged_in = login_acmp()
            if not logged_in:
                raise RuntimeError(
                    "Не удалось войти на acmp.ru — Accepted и проценты без сессии недоступны"
                )

            all_topics = [
                (sec_name, top_name, top_info)
                for sec_name, topics in COURSE_STRUCTURE.items()
                for top_name, top_info in topics.items()
            ]

            acc_set = set()
            problem_to_task = {}
            topic_totals = {}
            failed_topics = []

            def fetch_one(sec_name, top_name, top_info):
                topic_opener, _ = make_opener(clone_cookiejar(cookiejar))
                return fetch_topic(topic_opener, sec_name, top_name, top_info)

            with _cf.ThreadPoolExecutor(max_workers=8) as ex:
                futures = {
                    ex.submit(fetch_one, sec_name, top_name, top_info): (sec_name, top_name)
                    for sec_name, top_name, top_info in all_topics
                }
                for fut in _cf.as_completed(futures):
                    sec_name, top_name = futures[fut]
                    try:
                        local_acc, local_p2t, letters = fut.result()
                        acc_set.update(local_acc)
                        problem_to_task.update(local_p2t)
                        topic_totals[(sec_name, top_name)] = len(letters)
                    except Exception as exc:
                        failed_topics.append(f"{sec_name}/{top_name}: {exc}")

            if len(problem_to_task) < MIN_PARSED_PROBLEMS:
                raise RuntimeError(
                    f"С сайта курса прочитано слишком мало задач ({len(problem_to_task)}). "
                    + ("; ".join(failed_topics[:4]) if failed_topics else "Проверьте доступ к ACMP.")
                )

            accepted_dates = {}
            dates_error = ""
            try:
                accepted_dates = fetch_accepted_submission_dates(cookiejar, problem_to_task)
            except Exception as exc:
                dates_error = f"Даты сдач не загружены: {exc}"

            warning_parts = []
            if failed_topics:
                warning_parts.append("Не все темы: " + "; ".join(failed_topics[:5]))
            if dates_error:
                warning_parts.append(dates_error)

            last_sync_time = time.time()
            cached_acmp_data = {
                "accepted": acc_set,
                "accepted_dates": accepted_dates,
                "topic_totals": topic_totals,
                "sync_ok": not failed_topics,
                "logged_in": True,
                "sync_error": " | ".join(warning_parts),
                "synced_at": datetime.datetime.now().strftime("%H:%M:%S"),
            }
            log_sync(
                f"OK login, задач={len(problem_to_task)}, accepted={len(acc_set)}, "
                f"дат={len(accepted_dates)}"
            )
        except Exception as e:
            last_sync_time = time.time()
            cached_acmp_data = {
                **cached_acmp_data,
                "sync_ok": False,
                "logged_in": cached_acmp_data.get("logged_in", False),
                "sync_error": str(e),
                "synced_at": datetime.datetime.now().strftime("%H:%M:%S"),
            }
            log_sync(f"Ошибка синка: {e}")

        return cached_acmp_data


def get_stats_data(force=False):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    day_before = today - datetime.timedelta(days=2)

    acmp_data = sync_acmp_status(force=force)
    acc_set = acmp_data["accepted"]
    accepted_dates = acmp_data["accepted_dates"]
    topic_totals = acmp_data.get("topic_totals") or {}

    # 2. Сканирование локальных файлов
    all_files = []
    accepted_solved = []
    by_date_accepted = defaultdict(list)
    by_section_topic_accepted = defaultdict(lambda: defaultdict(list))
    local_by_task = {}

    for p in ROOT_DIR.rglob("*"):
        if not p.is_file():
            continue
        if p.name in IGNORED_NAMES or p.name.startswith("."):
            continue
        if p.suffix.lower() not in [".py", ".cpp", ".pas", ".c"]:
            continue
        if not re.fullmatch(r"[A-Z]", p.stem.upper()):
            continue

        rel = p.relative_to(ROOT_DIR)
        if "tools" in rel.parts or any(part.startswith(".") for part in rel.parts):
            continue

        try:
            stat = p.stat()
            file_size = stat.st_size
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
            file_date = mtime.date()
            
            parts = rel.parts
            section = parts[0] if len(parts) > 1 else "Корень"
            topic = parts[1] if len(parts) > 2 else section
            task_letter = p.stem.upper()
            task_key = (section, topic, task_letter)

            # Решено только если на ACMP у этой же темы/буквы стоит Accepted.
            is_accepted_on_acmp = task_key in acc_set
            accepted_date = accepted_dates.get(task_key)

            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                lines = len([l for l in content.splitlines() if l.strip()])
            except Exception:
                lines = 0

            # Определение статуса
            if is_accepted_on_acmp:
                status_code = "accepted"
                status_label = "✅ ACCEPTED (СДАНО)"
            elif file_size > 0:
                status_code = "draft"
                status_label = "📝 ЧЕРНОВИК (НЕ СДАНО НА ACMP)"
            else:
                status_code = "template"
                status_label = "⚪ ШАБЛОН (0 B)"

            item = {
                "name": p.name,
                "task_letter": task_letter,
                "rel_path": str(rel).replace("\\", "/"),
                "full_path": str(p),
                "section": section,
                "topic": topic,
                "size": file_size,
                "lines": lines,
                "status": status_code,
                "status_label": status_label,
                "is_accepted": is_accepted_on_acmp,
                "mtime": mtime.strftime("%H:%M:%S"),
                "datetime_str": mtime.strftime("%d.%m.%Y %H:%M:%S"),
                "date_str": file_date.strftime("%d.%m.%Y"),
                "date_iso": file_date.isoformat(),
                "accepted_date_str": accepted_date.strftime("%d.%m.%Y") if accepted_date else "",
                "accepted_date_iso": accepted_date.isoformat() if accepted_date else "",
                "timestamp": stat.st_mtime
            }

            all_files.append(item)
            local_by_task[task_key] = item

        except Exception:
            continue

    all_files.sort(key=lambda x: x["timestamp"], reverse=True)

    for sec_name, topics in COURSE_STRUCTURE.items():
        for top_name, top_info in topics.items():
            for letter_code in range(ord('A'), ord('A') + top_info["total"]):
                let = chr(letter_code)
                task_key = (sec_name, top_name, let)
                if task_key not in acc_set:
                    continue

                # Курс: только Accepted с сайта, не наличие локального файла.

                accepted_date = accepted_dates.get(task_key)
                local_item = local_by_task.get(task_key)
                item = dict(local_item) if local_item else {
                    "name": f"{let}.py",
                    "task_letter": let,
                    "rel_path": f"{sec_name}/{top_name}/{let}.py",
                    "full_path": "",
                    "section": sec_name,
                    "topic": top_name,
                    "size": 0,
                    "lines": 0,
                    "status": "accepted",
                    "status_label": "ACCEPTED",
                    "is_accepted": True,
                    "mtime": "",
                    "datetime_str": "",
                    "date_str": "",
                    "date_iso": "",
                    "timestamp": 0
                }
                item["accepted_date_str"] = accepted_date.strftime("%d.%m.%Y") if accepted_date else ""
                item["accepted_date_iso"] = accepted_date.isoformat() if accepted_date else ""
                item["is_accepted"] = True
                item["status"] = "accepted"

                accepted_solved.append(item)
                by_section_topic_accepted[sec_name][top_name].append(item)
                if accepted_date:
                    by_date_accepted[accepted_date].append(item)

    accepted_solved.sort(key=lambda x: x["timestamp"], reverse=True)

    today_items = by_date_accepted[today]
    yesterday_items = by_date_accepted[yesterday]
    day_before_items = by_date_accepted[day_before]

    # Стрик (по дням реальных сданных решений)
    streak = 0
    curr_d = today if len(today_items) > 0 else yesterday
    while curr_d in by_date_accepted and len(by_date_accepted[curr_d]) > 0:
        streak += 1
        curr_d -= datetime.timedelta(days=1)

    # 3. Детальный прогресс по курсу C++ (100% точный по Accepted на ACMP)
    course_data = []
    total_course_tasks = 0
    total_course_solved = 0

    for sec_name, topics in COURSE_STRUCTURE.items():
        sec_total = 0
        sec_solved = 0
        topic_list = []

        for top_name, top_info in topics.items():
            live_total = topic_totals.get((sec_name, top_name))
            top_total = live_total if live_total else top_info["total"]
            sec_total += top_total

            solved_letters = []
            for letter_code in range(ord('A'), ord('A') + top_total):
                let = chr(letter_code)
                if (sec_name, top_name, let) in acc_set:
                    solved_letters.append(let)

            solved_count = len(solved_letters)
            sec_solved += solved_count

            pct = round((solved_count / top_total * 100), 1) if top_total > 0 else 0
            topic_list.append({
                "name": top_name,
                "total": top_total,
                "solved_count": solved_count,
                "percent": pct,
                "tasks": solved_letters
            })

        total_course_tasks += sec_total
        total_course_solved += sec_solved
        sec_pct = round((sec_solved / sec_total * 100), 1) if sec_total > 0 else 0

        course_data.append({
            "section": sec_name,
            "total": sec_total,
            "solved": sec_solved,
            "percent": sec_pct,
            "topics": topic_list
        })

    total_course_percent = round((total_course_solved / total_course_tasks * 100), 1) if total_course_tasks > 0 else 0

    def summarize_day(items):
        by_top = defaultdict(list)
        for it in items:
            by_top[f"{it['section']} → {it['topic']}"].append(it)
        res = []
        for k, task_list in by_top.items():
            res.append({
                "category": k,
                "count": len(task_list),
                "tasks": [t["name"] for t in task_list],
                "items": task_list
            })
        return res

    history_days = []
    for i in range(14):
        d = today - datetime.timedelta(days=i)
        items = by_date_accepted[d]
        history_days.append({
            "date_iso": d.isoformat(),
            "date_str": d.strftime("%d.%m.%Y"),
            "day_name": "Сегодня" if i == 0 else ("Вчера" if i == 1 else ("Позавчера" if i == 2 else d.strftime("%a"))),
            "count": len(items),
            "summary": summarize_day(items)
        })

    return {
        "today_str": today.strftime("%d.%m.%Y"),
        "yesterday_str": yesterday.strftime("%d.%m.%Y"),
        "day_before_str": day_before.strftime("%d.%m.%Y"),
        "today_count": len(today_items),
        "yesterday_count": len(yesterday_items),
        "day_before_count": len(day_before_items),
        "today_breakdown": summarize_day(today_items),
        "yesterday_breakdown": summarize_day(yesterday_items),
        "day_before_breakdown": summarize_day(day_before_items),
        "streak": streak,
        "total_solved": len(accepted_solved),
        "course": {
            "name": "Язык программирования C++ (решения на Python)",
            "total_tasks": total_course_tasks,
            "solved_tasks": total_course_solved,
            "percent": total_course_percent,
            "sections": course_data
        },
        "history": history_days,
        "all_recent": all_files[:35],
        "sync": {
            "ok": bool(acmp_data.get("sync_ok")),
            "logged_in": bool(acmp_data.get("logged_in")),
            "error": acmp_data.get("sync_error") or "",
            "at": acmp_data.get("synced_at") or "",
        },
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACMP Glass Tracker — Статистика курса C++</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #08090c;
            --glass-bg: rgba(16, 20, 28, 0.65);
            --glass-card: rgba(22, 28, 38, 0.55);
            --glass-card-hover: rgba(30, 38, 52, 0.85);
            --glass-border: rgba(0, 255, 128, 0.16);
            --glass-border-bright: rgba(0, 255, 128, 0.45);
            
            --lime: #00ff7f;
            --lime-glow: rgba(0, 255, 127, 0.28);
            --lime-dim: #00b359;
            --mint: #10b981;
            --cyan: #06b6d4;
            --yellow: #facc15;
            --red: #f87171;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --text-dark: #64748b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
        }

        body {
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(0, 255, 127, 0.09) 0%, transparent 40%),
                radial-gradient(circle at 90% 30%, rgba(6, 182, 212, 0.07) 0%, transparent 45%),
                radial-gradient(circle at 50% 85%, rgba(0, 255, 127, 0.06) 0%, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
            overflow-x: hidden;
        }

        .container {
            max-width: 1300px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding: 20px 28px;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        .logo-box {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--lime), #059669);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 20px var(--lime-glow);
        }

        .logo-text h1 {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #ffffff, var(--lime));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-text p {
            font-size: 13px;
            color: var(--text-muted);
            font-weight: 400;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .live-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 255, 127, 0.1);
            border: 1px solid rgba(0, 255, 127, 0.3);
            color: var(--lime);
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            max-width: 420px;
        }

        .live-badge.error {
            background: rgba(248, 113, 113, 0.12);
            border-color: rgba(248, 113, 113, 0.4);
            color: var(--red);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background: var(--lime);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--lime);
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.6; }
            50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 14px var(--lime); }
            100% { transform: scale(0.95); opacity: 0.6; }
        }

        .btn-refresh {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-refresh:hover {
            background: var(--lime);
            color: #000;
            border-color: var(--lime);
            box-shadow: 0 0 15px var(--lime-glow);
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 28px;
        }

        .day-card {
            background: var(--glass-bg);
            backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 25px rgba(0,0,0,0.35);
        }

        .day-card:hover {
            border-color: var(--glass-border-bright);
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(0, 255, 127, 0.14);
        }

        .day-card.today {
            border-color: rgba(0, 255, 127, 0.4);
            background: linear-gradient(145deg, rgba(16, 28, 22, 0.75), rgba(12, 16, 24, 0.85));
            box-shadow: 0 10px 30px rgba(0, 255, 127, 0.18);
        }

        .day-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .day-tag {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 10px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
        }

        .day-card.today .day-tag {
            background: rgba(0, 255, 127, 0.15);
            color: var(--lime);
            border: 1px solid rgba(0, 255, 127, 0.3);
        }

        .day-count {
            font-size: 48px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1;
            margin-bottom: 8px;
        }

        .day-card.today .day-count {
            color: var(--lime);
            text-shadow: 0 0 25px var(--lime-glow);
        }

        .day-label {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 18px;
        }

        .day-folders {
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            padding-top: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 240px;
            overflow-y: auto;
        }

        .folder-item {
            background: var(--glass-card);
            padding: 10px 14px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }

        .folder-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
        }

        .folder-count {
            color: var(--lime);
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
        }

        .folder-tasks {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .task-chip {
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .task-chip.accepted {
            background: rgba(0, 255, 127, 0.15);
            color: var(--lime);
            border: 1px solid rgba(0, 255, 127, 0.3);
        }

        .task-chip.draft {
            background: rgba(250, 204, 21, 0.12);
            color: var(--yellow);
            border: 1px solid rgba(250, 204, 21, 0.3);
        }

        .course-section {
            background: var(--glass-bg);
            backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 28px;
            margin-bottom: 28px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }

        .course-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .course-title h2 {
            font-size: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .course-title p {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .course-meta {
            text-align: right;
        }

        .course-pct {
            font-size: 32px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: var(--lime);
            text-shadow: 0 0 20px var(--lime-glow);
        }

        .course-ratio {
            font-size: 13px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }

        .progress-bar-wrap {
            height: 12px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 28px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #059669, var(--lime));
            border-radius: 20px;
            box-shadow: 0 0 15px var(--lime-glow);
            transition: width 0.8s ease;
        }

        .sections-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(370px, 1fr));
            gap: 16px;
        }

        .sec-card {
            background: var(--glass-card);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 16px 20px;
            transition: all 0.2s;
        }

        .sec-card:hover {
            background: var(--glass-card-hover);
            border-color: var(--glass-border);
        }

        .sec-card.active {
            border-color: rgba(0, 255, 127, 0.35);
        }

        .sec-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .sec-name {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
        }

        .sec-badge {
            font-size: 12px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            padding: 3px 8px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
        }

        .sec-badge.completed {
            background: rgba(0, 255, 127, 0.15);
            color: var(--lime);
            border: 1px solid rgba(0, 255, 127, 0.3);
        }

        .sec-bar {
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 12px;
        }

        .sec-bar-fill {
            height: 100%;
            background: var(--lime);
            border-radius: 10px;
        }

        .topics-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .topic-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-muted);
            padding: 4px 6px;
            border-radius: 6px;
            background: rgba(0,0,0,0.25);
        }

        .topic-name {
            font-weight: 500;
        }

        .topic-stat {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-main);
        }

        .topic-stat.full {
            color: var(--lime);
            font-weight: 700;
        }

        .live-table-sec {
            background: var(--glass-bg);
            backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 28px;
        }

        .table-title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .table-wrap {
            overflow-x: auto;
        }

        table.glass-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        table.glass-table th {
            text-align: left;
            padding: 12px 16px;
            color: var(--text-muted);
            font-weight: 600;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        table.glass-table td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }

        table.glass-table tr:hover td {
            background: rgba(255, 255, 255, 0.03);
        }

        .feed-section {
            background: var(--glass-bg);
            backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px;
        }

        .feed-header {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .history-timeline {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .history-row {
            display: grid;
            grid-template-columns: 140px 100px 1fr;
            align-items: center;
            background: var(--glass-card);
            padding: 12px 18px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 13px;
        }

        .hist-date {
            font-weight: 600;
            color: var(--text-main);
        }

        .hist-count {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            color: var(--lime);
        }

        .hist-desc {
            color: var(--text-muted);
            font-size: 12px;
        }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); }
        ::-webkit-scrollbar-thumb { background: rgba(0, 255, 127, 0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--lime); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-box">
                <div class="logo-icon">⚡</div>
                <div class="logo-text">
                    <h1>ACMP GLASS TRACKER</h1>
                    <p>Курс: Язык программирования C++ • Синхронизация с ACMP (Только Accepted)</p>
                </div>
            </div>
            <div class="header-actions">
                <div class="live-badge">
                    <span class="pulse-dot"></span>
                    <span id="liveTime">ACMP VERIFIED SYNC</span>
                </div>
                <button class="btn-refresh" onclick="fetchData(true)">🔄 Обновить с ACMP</button>
            </div>
        </header>

        <div class="comparison-grid">
            <div class="day-card today">
                <div class="day-card-header">
                    <span class="day-tag">СЕГОДНЯ</span>
                    <span class="day-label" id="todayDateStr">18.09.2026</span>
                </div>
                <div class="day-count" id="todayCount">0</div>
                <div class="day-label">задач курса C++ сдано сегодня (Accepted на ACMP)</div>
                <div class="day-folders" id="todayFolders"></div>
            </div>

            <div class="day-card">
                <div class="day-card-header">
                    <span class="day-tag">ВЧЕРА</span>
                    <span class="day-label" id="yesterdayDateStr">17.09.2026</span>
                </div>
                <div class="day-count" id="yesterdayCount">0</div>
                <div class="day-label">задач курса C++ сдано вчера</div>
                <div class="day-folders" id="yesterdayFolders"></div>
            </div>

            <div class="day-card">
                <div class="day-card-header">
                    <span class="day-tag">ПОЗАВЧЕРА</span>
                    <span class="day-label" id="dayBeforeDateStr">16.09.2026</span>
                </div>
                <div class="day-count" id="dayBeforeCount">0</div>
                <div class="day-label">задач курса C++ сдано позавчера</div>
                <div class="day-folders" id="dayBeforeFolders"></div>
            </div>
        </div>

        <div class="course-section">
            <div class="course-header">
                <div class="course-title">
                    <h2>🏆 Прогресс курса: Язык программирования C++</h2>
                    <p>Проценты считаются по жирным (Accepted) задачам на страницах тем acmp.ru</p>
                </div>
                <div class="course-meta">
                    <div class="course-pct" id="coursePct">0%</div>
                    <div class="course-ratio" id="courseRatio">0 / 239 задач</div>
                </div>
            </div>
            
            <div class="progress-bar-wrap">
                <div class="progress-bar-fill" id="courseBarFill" style="width: 0%"></div>
            </div>

            <div class="sections-grid" id="sectionsGrid"></div>
        </div>

        <div class="live-table-sec">
            <div class="table-title">
                <span>📁 Локальные файлы и статус проверки на ACMP</span>
                <span style="font-size: 12px; color: var(--text-muted); font-weight: 400;">Зелёный = Accepted на ACMP. Текст в файле сам по себе задачу не сдаёт.</span>
            </div>
            <div class="table-wrap">
                <table class="glass-table">
                    <thead>
                        <tr>
                            <th>Файл</th>
                            <th>Раздел и Тема</th>
                            <th>Время изменения</th>
                            <th>Строк</th>
                            <th>Размер</th>
                            <th>Статус на ACMP</th>
                        </tr>
                    </thead>
                    <tbody id="filesTableBody"></tbody>
                </table>
            </div>
        </div>

        <div class="feed-section">
            <div class="feed-header">
                <span>📊 Динамика по дням (История Accepted)</span>
            </div>
            <div class="history-timeline" id="historyTimeline"></div>
        </div>
    </div>

    <script>
        async function fetchData(force) {
            try {
                const res = await fetch('/api/stats' + (force ? '?force=1' : ''));
                const data = await res.json();
                renderData(data);
            } catch (e) {
                console.error("Ошибка загрузки данных:", e);
            }
        }

        function renderData(data) {
            document.getElementById('todayCount').innerText = data.today_count;
            document.getElementById('todayDateStr').innerText = data.today_str;
            document.getElementById('yesterdayCount').innerText = data.yesterday_count;
            document.getElementById('yesterdayDateStr').innerText = data.yesterday_str || '';
            document.getElementById('dayBeforeCount').innerText = data.day_before_count;
            document.getElementById('dayBeforeDateStr').innerText = data.day_before_str || '';

            const badge = document.querySelector('.live-badge');
            const liveTime = document.getElementById('liveTime');
            const sync = data.sync || {};
            if (sync.ok) {
                badge.classList.remove('error');
                liveTime.innerText = 'ACMP ' + (sync.at ? sync.at : 'OK');
            } else {
                badge.classList.add('error');
                liveTime.innerText = sync.error ? ('Ошибка: ' + sync.error) : 'Нет синка с ACMP';
            }

            renderFolders('todayFolders', data.today_breakdown);
            renderFolders('yesterdayFolders', data.yesterday_breakdown);
            renderFolders('dayBeforeFolders', data.day_before_breakdown);

            document.getElementById('coursePct').innerText = data.course.percent + '%';
            document.getElementById('courseRatio').innerText = `${data.course.solved_tasks} / ${data.course.total_tasks} задач`;
            document.getElementById('courseBarFill').style.width = data.course.percent + '%';

            const secGrid = document.getElementById('sectionsGrid');
            secGrid.innerHTML = '';
            data.course.sections.forEach(sec => {
                const isCompleted = sec.percent >= 100;
                const secCard = document.createElement('div');
                secCard.className = `sec-card ${sec.solved > 0 ? 'active' : ''}`;
                
                let topicsHtml = '';
                sec.topics.forEach(t => {
                    const isFull = t.solved_count >= t.total;
                    topicsHtml += `
                        <div class="topic-row">
                            <span class="topic-name">${t.name}</span>
                            <span class="topic-stat ${isFull ? 'full' : ''}">${t.solved_count}/${t.total} (${t.percent}%)</span>
                        </div>
                    `;
                });

                secCard.innerHTML = `
                    <div class="sec-head">
                        <span class="sec-name">${sec.section}</span>
                        <span class="sec-badge ${isCompleted ? 'completed' : ''}">${sec.solved}/${sec.total} (${sec.percent}%)</span>
                    </div>
                    <div class="sec-bar">
                        <div class="sec-bar-fill" style="width: ${sec.percent}%"></div>
                    </div>
                    <div class="topics-list">
                        ${topicsHtml}
                    </div>
                `;
                secGrid.appendChild(secCard);
            });

            const tbody = document.getElementById('filesTableBody');
            tbody.innerHTML = '';
            data.all_recent.forEach(f => {
                const tr = document.createElement('tr');
                const isAcc = f.is_accepted;
                tr.innerHTML = `
                    <td style="font-weight: 600; color: var(--text-main); font-family: 'JetBrains Mono', monospace;">${f.name}</td>
                    <td style="color: var(--text-muted);">${f.section} → ${f.topic}</td>
                    <td style="color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">${f.mtime} (${f.date_str})</td>
                    <td style="font-family: 'JetBrains Mono', monospace;">${f.lines}</td>
                    <td style="font-family: 'JetBrains Mono', monospace;">${f.size} B</td>
                    <td>
                        <span class="task-chip ${isAcc ? 'accepted' : 'draft'}">
                            ${isAcc ? '✅ ACCEPTED' : '📝 ЧЕРНОВИК (НЕ СДАНО)'}
                        </span>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            const histTimeline = document.getElementById('historyTimeline');
            histTimeline.innerHTML = '';
            data.history.forEach(h => {
                if (h.count === 0 && h.day_name !== 'Сегодня' && h.day_name !== 'Вчера') return;
                
                const summaryText = h.summary.map(s => `${s.category} (${s.tasks.join(', ')})`).join(' • ') || 'Нет сданных задач';
                
                const row = document.createElement('div');
                row.className = 'history-row';
                row.innerHTML = `
                    <div class="hist-date">${h.date_str} (${h.day_name})</div>
                    <div class="hist-count">${h.count} задач</div>
                    <div class="hist-desc">${summaryText}</div>
                `;
                histTimeline.appendChild(row);
            });
        }

        function renderFolders(containerId, breakdown) {
            const cont = document.getElementById(containerId);
            cont.innerHTML = '';
            if (!breakdown || breakdown.length === 0) {
                cont.innerHTML = '<div style="color: var(--text-dark); font-size: 12px; padding: 8px;">Нет сданных задач за этот день</div>';
                return;
            }

            breakdown.forEach(item => {
                const chips = item.items.map(t => `<span class="task-chip accepted">${t.name}</span>`).join('');
                const div = document.createElement('div');
                div.className = 'folder-item';
                div.innerHTML = `
                    <div class="folder-title">
                        <span>📁 ${item.category}</span>
                        <span class="folder-count">+${item.count}</span>
                    </div>
                    <div class="folder-tasks">${chips}</div>
                `;
                cont.appendChild(div);
            });
        }

        fetchData(true);
        setInterval(() => fetchData(false), 30000);
    </script>
</body>
</html>
"""

class TrackerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/stats":
            qs = urllib.parse.parse_qs(parsed.query)
            force = (qs.get("force", ["0"])[0] or "").lower() in ("1", "true", "yes")
            data = get_stats_data(force=force)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=7860, open_browser=True):
    server = HTTPServer(("127.0.0.1", port), TrackerHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"\n⚡ ACMP Glass Tracker запущен: {url}")
    print("Кэш ACMP 3 минуты. Кнопка «Обновить с ACMP» форсирует синк.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановка трекера...")

if __name__ == "__main__":
    run_server(port=7860, open_browser=True)
