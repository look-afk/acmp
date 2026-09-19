h,a,b = map(int,input().split())
s = 0
d = 1
while True:
    s +=a
    if s >= h:
        break
    s -= b
    d += 1
print(d)