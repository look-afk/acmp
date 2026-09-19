ans = []
l = map(int,input().split())
for i in l:
    if i == 0:
        break
    elif i%2 == 0:
        ans.append(i)

print(len(ans))