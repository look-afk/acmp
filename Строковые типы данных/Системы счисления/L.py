def to_int(s):
    fibs = [1, 2]
    while len(fibs) < len(s):
        fibs.append(fibs[-1] + fibs[-2])
    n = 0
    s = s[::-1]
    for i, ch in enumerate(s):
        if ch == '1':
            n += fibs[i]
    return n

def to_fib(n):
    if n == 0:
        return '0'
    fibs = [1, 2]
    while fibs[-1] <= n:
        fibs.append(fibs[-1] + fibs[-2])
    bits = {}
    for i in range(len(fibs) - 1, -1, -1):
        if fibs[i] <= n:
            bits[i] = 1
            n -= fibs[i]
    top = max(bits)
    return ''.join(str(bits.get(j, 0)) for j in range(top, -1, -1))

a = input().strip()
b = input().strip()
print(to_fib(to_int(a) + to_int(b)))
