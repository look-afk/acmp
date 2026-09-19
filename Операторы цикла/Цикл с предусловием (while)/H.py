x, y = map(float, input().split())
day = 1

while x < y - 1e-7:
    x *= 1.15
    day += 1

print(day)