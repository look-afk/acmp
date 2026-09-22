c, n = input().split()
n = int(n)
digits = []
while n != 0:
    r = n % 3
    if r == 2:
        digits.append(-1)
        n = n // 3 + 1
    else:
        digits.append(r)
        n = n // 3
L, R = [], []
for i, d in enumerate(digits):
    if d == 0:
        continue
    w = 3 ** i
    if c == 'L':
        if d == 1:
            R.append(w)
        else:
            L.append(w)
    else:
        if d == 1:
            L.append(w)
        else:
            R.append(w)
print('L:' + (' '.join(map(str, L)) if L else ''))
print('R:' + (' '.join(map(str, R)) if R else ''))
