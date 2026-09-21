k = []
n = []

for x in map(int, input().split()):
    if x == 0:
        break
    n.append(x)

for i in range(1,len(n)-1):
    if n[i] > n[i+1] and n[i] > n[i-1]:
        k.append(i)
if len(k) < 2: 
    print(0)
else:
    m = min(k[j] - k[j - 1] for j in range(1, len(k)))
    print(m)