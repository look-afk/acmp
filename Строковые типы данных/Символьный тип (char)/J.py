s = input().strip()
best = cur = 0
for c in s:
    if c == '0':
        cur += 1
        best = max(best, cur)
    else:
        cur = 0
print(best)
