n = int(input())
good = []
for b in range(2, 37):
    x = n
    d = []
    while x:
        d.append(x % b)
        x //= b
    if not d:
        d = [0]
    if d == d[::-1]:
        good.append(b)
if not good:
    print('none')
elif len(good) == 1:
    print('unique')
    print(good[0])
else:
    print('multiple')
    print(*good)
