a, b, c, d, e, f = map(int, input().split())
lis1 = [a, b, c]
lis2 = [d, e, f]
n = max(lis1) * max(lis2)
lis1.remove(max(lis1))
lis2.remove(max(lis2))
k = max(lis1) * max(lis2)
lis1.remove(max(lis1))
lis2.remove(max(lis2))
c = lis1[0] * lis2[0]
print(n + k + c)