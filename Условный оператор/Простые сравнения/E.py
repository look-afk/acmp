n = 0
m = 0
a,b = list(map(int,input().split()))
n+=a
m+=b
a,b = list(map(int,input().split()))
n+=a
m+=b
a,b = list(map(int,input().split()))
n+=a
m+=b
a,b = list(map(int,input().split()))
n+=a
m+=b
print(1 if n > m else "DRAW" if n == m else 2)