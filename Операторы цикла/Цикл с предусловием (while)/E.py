n = int(input())
if n == 0:
    print(0)
elif n == 1:
    print(1)
else:
    a, b = 0, 1
    i = 2
    while i <= n:
        a, b = b, a + b
        i += 1
    print(b)
