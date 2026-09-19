s = input()
m =s[:3]
a=s[3:]
m = list(map(int,m))
m = sum(m)
a = list(map(int,a))
a = sum(a)
if m == a:
    print("YES")
else:
    print("NO")
