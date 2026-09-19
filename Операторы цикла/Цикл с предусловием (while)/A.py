n = int(input())
l = []
for i in range(1,n+1):
    if i**2 > n:
        break
    l.append(i**2)
print(*l)