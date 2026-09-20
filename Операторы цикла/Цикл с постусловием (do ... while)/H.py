s = list(map(int,input().split()))
a = []
for i in s:
    if i == 0:
        break
    a.append(i)
a.remove(max(a))
print((max(a)))