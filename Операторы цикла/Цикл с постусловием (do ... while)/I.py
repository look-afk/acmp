s = list(map(int, input().split()))
a = []
for i in s:
    if i == 0 and a and a[-1] == 0:
        break
    a.append(i)

print(sum(a))