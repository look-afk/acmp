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

def _normalize_name(s):
    """Делает сравнение имён папок с курсом нечувствительным к регистру/пробелам."""
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("ё", "е")
    return s


# (нормализованное_название_раздела, нормализованное_название_темы) -> точные имена из COURSE_STRUCTURE.
# Нужно, чтобы папки на диске сопоставлялись с курсом, даже если в их названии
# лишний пробел, другой регистр или "ё"/"е" вместо друг друга.
CANONICAL_SEC_TOP = {}
for _sec_name, _topics in COURSE_STRUCTURE.items():
    for _top_name in _topics:
        CANONICAL_SEC_TOP[(_normalize_name(_sec_name), _normalize_name(_top_name))] = (_sec_name, _top_name)


IGNORED_NAMES = {
    "manage.py", "tracker.py", "app.py", "Fill.py", "refill.py", "backup.py",
    "test_acmp_sync.py", "test_run.py", "Запустить_Трекер.bat", "main.py", "f1.py"
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CACHE_TTL_SEC = 60
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
    unmatched_folders = []
    unmatched_folders_seen = set()

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
            section_raw = parts[0] if len(parts) > 1 else "Корень"
            topic_raw = parts[1] if len(parts) > 2 else section_raw
            canon = CANONICAL_SEC_TOP.get((_normalize_name(section_raw), _normalize_name(topic_raw)))
            if canon:
                section, topic = canon
            else:
                section, topic = section_raw, topic_raw
                if (section_raw, topic_raw) not in unmatched_folders_seen:
                    unmatched_folders_seen.add((section_raw, topic_raw))
                    unmatched_folders.append({"section": section_raw, "topic": topic_raw})
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
        "unmatched_folders": unmatched_folders,
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ACMP Tracker — C++</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#0b0c10;
  --panel:#131419;
  --panel-2:#181a21;
  --border:#23252e;
  --border-soft:#1b1d25;
  --text:#eceef2;
  --text-muted:#8a8d98;
  --text-dim:#5c5f6b;
  --accent:#6d7bff;
  --accent-soft:rgba(109,123,255,0.14);
  --good:#2ecc8f;
  --good-soft:rgba(46,204,143,0.14);
  --warn:#f2b84b;
  --bad:#f2555a;
  --radius:14px;
}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;}
body{
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  padding:28px 32px 60px;
}
.mono{font-family:'JetBrains Mono',monospace;}
.wrap{max-width:1180px;margin:0 auto;}

/* header */
header{
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:22px;flex-wrap:wrap;gap:14px;
}
.title-block{display:flex;align-items:center;gap:12px;}
.title-icon{
  width:38px;height:38px;border-radius:10px;
  background:linear-gradient(135deg,var(--accent),#4a56d6);
  display:flex;align-items:center;justify-content:center;font-size:18px;
}
.title-block h1{font-size:19px;font-weight:700;letter-spacing:-0.2px;}
.title-block p{font-size:12.5px;color:var(--text-muted);margin-top:1px;}

.status-row{display:flex;align-items:center;gap:10px;}
.sync-pill{
  display:flex;align-items:center;gap:7px;
  background:var(--panel);border:1px solid var(--border);
  padding:7px 13px;border-radius:30px;font-size:12px;color:var(--text-muted);
  max-width:360px;
}
.sync-pill .dot{width:7px;height:7px;border-radius:50%;background:var(--good);flex:none;}
.sync-pill.bad .dot{background:var(--bad);}
.sync-pill span.msg{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.btn{
  background:var(--panel);border:1px solid var(--border);color:var(--text);
  padding:8px 15px;border-radius:10px;cursor:pointer;font-size:13px;font-weight:600;
  display:flex;align-items:center;gap:7px;transition:.15s;
}
.btn:hover{background:var(--accent);border-color:var(--accent);color:#fff;}
.btn.spinning svg{animation:spin 0.8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}

/* KPI row */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}
.kpi{
  background:var(--panel);border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 20px;
}
.kpi .label{font-size:12px;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:.4px;}
.kpi .value{font-size:30px;font-weight:800;margin-top:6px;font-family:'JetBrains Mono',monospace;}
.kpi .sub{font-size:12px;color:var(--text-dim);margin-top:3px;}
.kpi.accent .value{color:var(--good);}
.kpi.streak .value{color:var(--warn);}

/* tabs */
.tabs{display:flex;gap:6px;margin-bottom:18px;border-bottom:1px solid var(--border);}
.tab{
  padding:10px 16px;font-size:13.5px;font-weight:600;color:var(--text-muted);
  cursor:pointer;border-bottom:2px solid transparent;transition:.15s;
}
.tab:hover{color:var(--text);}
.tab.active{color:var(--text);border-bottom-color:var(--accent);}
.panel{display:none;}
.panel.active{display:block;}

.card{
  background:var(--panel);border:1px solid var(--border);border-radius:var(--radius);
  padding:22px;margin-bottom:16px;
}
.card h3{font-size:14.5px;font-weight:700;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;}
.card h3 .hint{font-size:11.5px;color:var(--text-dim);font-weight:500;}

/* overview grid */
.overview-grid{display:grid;grid-template-columns:260px 1fr;gap:16px;}
@media(max-width:820px){.overview-grid{grid-template-columns:1fr;}}
.ring-wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;}
.ring-pct{font-size:34px;font-weight:800;font-family:'JetBrains Mono',monospace;}
.ring-sub{font-size:12.5px;color:var(--text-muted);text-align:center;}

.day-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:4px;}
.day-box{
  background:var(--panel-2);border:1px solid var(--border-soft);border-radius:10px;padding:12px 14px;
}
.day-box .n{font-size:22px;font-weight:800;font-family:'JetBrains Mono',monospace;}
.day-box .l{font-size:11.5px;color:var(--text-muted);margin-bottom:2px;}
.day-box.today{border-color:rgba(109,123,255,0.4);background:var(--accent-soft);}

/* sections */
.sec-card{
  background:var(--panel-2);border:1px solid var(--border-soft);border-radius:12px;
  padding:16px 18px;margin-bottom:10px;
}
.sec-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}
.sec-head .name{font-weight:700;font-size:14px;}
.sec-head .stat{font-size:12.5px;color:var(--text-muted);font-family:'JetBrains Mono',monospace;}
.bar-track{height:6px;background:var(--border);border-radius:4px;overflow:hidden;margin-bottom:12px;}
.bar-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--good));border-radius:4px;}
.topics{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px 16px;}
.topic-row{display:flex;justify-content:space-between;font-size:12.5px;padding:4px 0;color:var(--text-muted);border-bottom:1px dashed var(--border-soft);}
.topic-row .t{color:var(--text);}
.topic-row .v.full{color:var(--good);font-weight:700;}

/* table */
table{width:100%;border-collapse:collapse;font-size:13px;}
th{text-align:left;font-size:11.5px;color:var(--text-dim);text-transform:uppercase;letter-spacing:.4px;padding:8px 10px;border-bottom:1px solid var(--border);}
td{padding:9px 10px;border-bottom:1px solid var(--border-soft);color:var(--text-muted);}
td.name{color:var(--text);font-weight:600;font-family:'JetBrains Mono',monospace;}
.chip{padding:3px 9px;border-radius:6px;font-size:11.5px;font-weight:700;white-space:nowrap;}
.chip.accepted{background:var(--good-soft);color:var(--good);}
.chip.draft{background:rgba(242,184,75,0.12);color:var(--warn);}
.table-scroll{max-height:520px;overflow-y:auto;}

/* history */
.hist-row{
  display:grid;grid-template-columns:140px 70px 1fr;gap:14px;align-items:start;
  padding:10px 0;border-bottom:1px solid var(--border-soft);font-size:13px;
}
.hist-row .d{color:var(--text);font-weight:600;}
.hist-row .n{font-family:'JetBrains Mono',monospace;color:var(--good);font-weight:700;}
.hist-row .desc{color:var(--text-muted);font-size:12.5px;line-height:1.5;}

.empty{color:var(--text-dim);font-size:13px;padding:14px 0;text-align:center;}
canvas{max-height:260px;}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="title-block">
      <div class="title-icon">▲</div>
      <div>
        <h1>ACMP Tracker</h1>
        <p>Курс C++ · прогресс и статистика</p>
      </div>
    </div>
    <div class="status-row">
      <div class="sync-pill" id="syncPill">
        <div class="dot"></div>
        <span class="msg" id="syncMsg">Синхронизация…</span>
      </div>
      <button class="btn" id="refreshBtn" onclick="fetchData(true)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg>
        Обновить
      </button>
    </div>
  </header>

  <div class="card" id="mismatchWarning" style="display:none;border-color:rgba(242,184,75,0.4);background:rgba(242,184,75,0.08);">
    <h3 style="color:var(--warn);">⚠ Папки не совпадают с темами курса</h3>
    <p style="font-size:12.5px;color:var(--text-muted);line-height:1.6;">
      Файлы в этих папках не привязываются к прогрессу курса, даже если задача Accepted на ACMP —
      название папки должно точь-в-точь совпадать с разделом/темой курса. Переименуй папку или перенеси файл.
    </p>
    <div id="mismatchList" style="margin-top:10px;font-size:12.5px;font-family:'JetBrains Mono',monospace;color:var(--warn);"></div>
  </div>

  <div class="kpis">
    <div class="kpi accent">
      <div class="label" id="todayDateStr">Сегодня</div>
      <div class="value" id="todayCount">0</div>
      <div class="sub">задач Accepted</div>
    </div>
    <div class="kpi">
      <div class="label" id="yesterdayDateStr">Вчера</div>
      <div class="value" id="yesterdayCount">0</div>
      <div class="sub">задач Accepted</div>
    </div>
    <div class="kpi streak">
      <div class="label">Стрик</div>
      <div class="value" id="streakVal">0 дн.</div>
      <div class="sub">подряд с решениями</div>
    </div>
    <div class="kpi">
      <div class="label">Всего решено</div>
      <div class="value" id="totalSolved">0</div>
      <div class="sub" id="courseRatio">— / — задач курса</div>
    </div>
  </div>

  <div class="tabs">
    <div class="tab active" data-tab="overview">Обзор</div>
    <div class="tab" data-tab="sections">Разделы курса</div>
    <div class="tab" data-tab="history">История</div>
    <div class="tab" data-tab="files">Файлы</div>
  </div>

  <div class="panel active" id="panel-overview">
    <div class="overview-grid">
      <div class="card ring-wrap">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r="68" fill="none" stroke="var(--border)" stroke-width="14"/>
          <circle id="ringFill" cx="80" cy="80" r="68" fill="none" stroke="url(#ringGrad)" stroke-width="14"
            stroke-linecap="round" stroke-dasharray="427" stroke-dashoffset="427" transform="rotate(-90 80 80)"/>
          <defs>
            <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#6d7bff"/>
              <stop offset="100%" stop-color="#2ecc8f"/>
            </linearGradient>
          </defs>
        </svg>
        <div class="ring-pct" id="coursePct">0%</div>
        <div class="ring-sub">пройдено курса</div>
      </div>
      <div class="card">
        <h3>Последние 3 дня <span class="hint">по дате Accepted на ACMP</span></h3>
        <div class="day-strip">
          <div class="day-box today">
            <div class="l">Сегодня</div>
            <div class="n" id="dToday">0</div>
          </div>
          <div class="day-box">
            <div class="l">Вчера</div>
            <div class="n" id="dYesterday">0</div>
          </div>
          <div class="day-box">
            <div class="l">Позавчера</div>
            <div class="n" id="dBefore">0</div>
          </div>
        </div>
        <div style="margin-top:16px;">
          <canvas id="historyChart" height="90"></canvas>
        </div>
      </div>
    </div>
  </div>

  <div class="panel" id="panel-sections">
    <div class="card" id="sectionsCard">
      <h3>Прогресс по разделам</h3>
      <div id="sectionsList"></div>
    </div>
  </div>

  <div class="panel" id="panel-history">
    <div class="card">
      <h3>Динамика по дням</h3>
      <div id="historyTimeline"></div>
    </div>
  </div>

  <div class="panel" id="panel-files">
    <div class="card">
      <h3>Локальные файлы решений <span class="hint">зелёный = подтверждено Accepted на ACMP</span></h3>
      <div class="table-scroll">
        <table>
          <thead>
            <tr><th>Файл</th><th>Раздел / Тема</th><th>Изменён</th><th>Строк</th><th>Статус</th></tr>
          </thead>
          <tbody id="filesTableBody"></tbody>
        </table>
      </div>
    </div>
  </div>

</div>

<script>
let historyChart = null;

function setActiveTab(name){
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + name));
}
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => setActiveTab(t.dataset.tab)));

async function fetchData(force){
  const btn = document.getElementById('refreshBtn');
  if (force) btn.classList.add('spinning');
  try {
    const res = await fetch('/api/stats' + (force ? '?force=1' : ''));
    const data = await res.json();
    renderData(data);
  } catch (e) {
    console.error('Ошибка загрузки данных:', e);
  } finally {
    if (force) setTimeout(() => btn.classList.remove('spinning'), 400);
  }
}

function renderData(data){
  document.getElementById('todayDateStr').innerText = 'Сегодня, ' + data.today_str;
  document.getElementById('todayCount').innerText = data.today_count;
  document.getElementById('yesterdayDateStr').innerText = 'Вчера, ' + (data.yesterday_str || '');
  document.getElementById('yesterdayCount').innerText = data.yesterday_count;
  document.getElementById('streakVal').innerText = data.streak + ' дн.';
  document.getElementById('totalSolved').innerText = data.total_solved;
  document.getElementById('courseRatio').innerText = `${data.course.solved_tasks} / ${data.course.total_tasks} задач курса`;
  document.getElementById('dToday').innerText = data.today_count;
  document.getElementById('dYesterday').innerText = data.yesterday_count;
  document.getElementById('dBefore').innerText = data.day_before_count;

  const pill = document.getElementById('syncPill');
  const msg = document.getElementById('syncMsg');
  const sync = data.sync || {};
  if (sync.ok) {
    pill.classList.remove('bad');
    msg.innerText = 'Синк ACMP OK · ' + (sync.at || '');
  } else {
    pill.classList.add('bad');
    msg.innerText = sync.error ? ('Ошибка синка: ' + sync.error) : 'Нет синка с ACMP';
  }

  const pct = data.course.percent || 0;
  document.getElementById('coursePct').innerText = pct + '%';
  const circumference = 427;
  document.getElementById('ringFill').style.strokeDashoffset = circumference - (circumference * pct / 100);

  // mismatch warning
  const mw = document.getElementById('mismatchWarning');
  const ml = document.getElementById('mismatchList');
  if (data.unmatched_folders && data.unmatched_folders.length > 0) {
    mw.style.display = 'block';
    ml.innerHTML = data.unmatched_folders.map(f => `• ${f.section} / ${f.topic}`).join('<br>');
  } else {
    mw.style.display = 'none';
  }

  // sections
  const secList = document.getElementById('sectionsList');
  secList.innerHTML = '';
  data.course.sections.forEach(sec => {
    const div = document.createElement('div');
    div.className = 'sec-card';
    let topicsHtml = '';
    sec.topics.forEach(t => {
      const full = t.solved_count >= t.total;
      topicsHtml += `<div class="topic-row"><span class="t">${t.name}</span><span class="v ${full ? 'full' : ''}">${t.solved_count}/${t.total}</span></div>`;
    });
    div.innerHTML = `
      <div class="sec-head">
        <span class="name">${sec.section}</span>
        <span class="stat">${sec.solved}/${sec.total} · ${sec.percent}%</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${sec.percent}%"></div></div>
      <div class="topics">${topicsHtml}</div>
    `;
    secList.appendChild(div);
  });

  // files
  const tbody = document.getElementById('filesTableBody');
  tbody.innerHTML = '';
  if (!data.all_recent || data.all_recent.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">Файлы решений не найдены</td></tr>';
  }
  (data.all_recent || []).forEach(f => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="name">${f.name}</td>
      <td>${f.section} → ${f.topic}</td>
      <td class="mono">${f.mtime} (${f.date_str})</td>
      <td class="mono">${f.lines}</td>
      <td><span class="chip ${f.is_accepted ? 'accepted' : 'draft'}">${f.is_accepted ? 'Accepted' : 'Черновик'}</span></td>
    `;
    tbody.appendChild(tr);
  });

  // history timeline
  const hist = document.getElementById('historyTimeline');
  hist.innerHTML = '';
  (data.history || []).forEach(h => {
    const desc = h.summary.map(s => `${s.category} (${s.tasks.join(', ')})`).join(' · ') || 'Нет сданных задач';
    const row = document.createElement('div');
    row.className = 'hist-row';
    row.innerHTML = `
      <div class="d">${h.date_str}<br><span style="color:var(--text-dim);font-weight:400;">${h.day_name}</span></div>
      <div class="n">${h.count}</div>
      <div class="desc">${desc}</div>
    `;
    hist.appendChild(row);
  });

  // chart
  const labels = (data.history || []).slice().reverse().map(h => h.date_str.slice(0,5));
  const counts = (data.history || []).slice().reverse().map(h => h.count);
  const ctx = document.getElementById('historyChart').getContext('2d');
  if (historyChart) {
    historyChart.data.labels = labels;
    historyChart.data.datasets[0].data = counts;
    historyChart.update();
  } else {
    historyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: 'rgba(109,123,255,0.55)',
          borderRadius: 5,
          maxBarThickness: 26
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#8a8d98', font: { size: 11 } } },
          y: { beginAtZero: true, grid: { color: '#1b1d25' }, ticks: { color: '#8a8d98', font: { size: 11 }, precision: 0 } }
        }
      }
    });
  }
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