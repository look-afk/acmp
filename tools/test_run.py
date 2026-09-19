import sys, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'tools')
t0 = time.time()
from app import get_stats_data
d = get_stats_data()
elapsed = time.time() - t0
print(f"Done in {elapsed:.1f}s")
print(f"Today: {d['today_count']} | Yesterday: {d['yesterday_count']} | Day before: {d['day_before_count']}")
print(f"Total Accepted (course): {d['total_solved']}")
print(f"Course: {d['course']['solved_tasks']} / {d['course']['total_tasks']} = {d['course']['percent']}%")
print()
for sec in d['course']['sections']:
    print(f"  [{sec['solved']}/{sec['total']}] {sec['section']} ({sec['percent']}%)")
    for top in sec['topics']:
        if top['solved_count'] > 0:
            print(f"      {top['name']}: {top['solved_count']}/{top['total']} — {top['tasks']}")

