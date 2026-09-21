import math
n = []
k = 0
for x in map(int, input().split()):
    if x == 0:
        break
    n.append(x)
s = sum(n) / len(n)
for i in range(len(n)):
    ans = (n[i] - s)**2
    k += ans
k = math.sqrt(k/ (len(n) -1))
print(f"{k:.3f}")