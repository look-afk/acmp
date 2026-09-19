t = int(input())
l = []
for i in range(t):
    a,b = map(int,input().split())
    if b == 0:
        l.append(0)
    if b != 0:
        l.append(a)
if l.count(0) == t:
    print(-1)
else: 
    n = max(l)
    print(l.index(n)+1)