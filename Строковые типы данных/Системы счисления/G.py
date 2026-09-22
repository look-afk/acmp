n = int(input())
s = bin(n)[2:] if n else '0'
best = 0
for i in range(len(s)):
    r = s[i:] + s[:i]
    best = max(best, int(r, 2))
print(best)
