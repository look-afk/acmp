s = 0
ans = []
l = map(int,input().split())
for i in l:
    if i == 0:
        break
    elif i > s:
        s = i

print(s)