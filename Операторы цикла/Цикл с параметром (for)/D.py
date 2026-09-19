t = int(input())
l = list(map(int,input().split()))
crash = False
for i in l:
    if i <= 437:
        n = l.index(i)+1
        print(f"Crash {n}")
        crash = True
        break
if crash != True:
    print("No crash")

    