n, k = map(int, input().split())
ds = []
while n:
    ds.append(n % k)
    n //= k
if not ds:
    ds = [0]
p = 1
for d in ds:
    p *= d
print(p - sum(ds))
