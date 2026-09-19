l = list(map(int, input().split()))

count = 0
prev = None

for x in l:
    if x == 0:
        break
    if prev is not None and x > prev:
        count += 1
    prev = x  

print(count)