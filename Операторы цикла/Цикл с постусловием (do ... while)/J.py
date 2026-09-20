s = list(map(int, input().split()))
streak = 0
max_streak = 0
previous = None

for value in s:
    if value == 0:
        break

    if value == previous:
        streak += 1
    else:
        streak = 1

    max_streak = max(max_streak, streak)
    previous = value

print(max_streak)