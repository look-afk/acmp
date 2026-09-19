a,b,c, = list(map(int,input().split()))
if min(a,b,c) <= 93 or max(a,b,c) >= 728:
    print("Error")
else: 
    print(max(a,b,c))
