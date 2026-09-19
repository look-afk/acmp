l = {}
t = input()
for i in range(int(t)):
    a,b = map(int, input().split())
    l[a] = b
for n,m in l.items():
    d = 19*m +(n+239)*(n+366)//2
    print(d)
    
