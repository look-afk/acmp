a,b,c = map(int,input().split())
d,e,f = map(int,input().split())
s = 0
n = 0
for i in range(a):
    s += 3600
for i in range(b):
        s+= 60
s += c
for i in range(d):
    n += 3600
for i in range(e):
        n+= 60
n += f
z = n-s
print(z)