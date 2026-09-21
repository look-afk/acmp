def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a


n, m = map(int, input().split())

ans = n // gcd(n, m)

print(ans)