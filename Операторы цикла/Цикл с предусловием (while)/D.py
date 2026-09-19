n = int(input())
if n <= 0:
    print("NO")
else:
    ok = True
    while n > 1:
        if n % 2 != 0:
            ok = False
            break
        n //= 2
    print("YES" if ok else "NO")
