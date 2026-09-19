n = int(input())
a, b = 1, 1
pos = 1
while b < n:
    c = a + b
    a = b
    b = c
    pos += 1
if b == n:
    print(1)
    print(pos + 1)
else:
    print(0)
