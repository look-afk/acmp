n = int(input())
x = 0
k = []
while 2**x <= n:
    k.append(2**x)
    x += 1
print(*k)