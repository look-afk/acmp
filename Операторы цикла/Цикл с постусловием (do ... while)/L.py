k = 0
n = []

for x in map(int, input().split()):
    if x == 0:
        break
    n.append(x)

for i in range(1, len(n) - 1):
    if n[i] > n[i - 1] and n[i] > n[i + 1]:
        k += 1

print(k)
