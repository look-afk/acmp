a = int(input())
ans = 0
if a >= 1:
    for i in range(1,a+1):
        ans+=i
else:
    for i in range(a,2):
        ans+=i
print(ans)