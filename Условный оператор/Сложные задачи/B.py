k, w = map(int, input().split())
a1, b1, a2, b2, a3, b3 = map(int, input().split())

variants = [
    a1 <= w and b1 >= k,                   # 1 палатка
    a2 <= w and b2 >= k,                   # 2 палатка
    a3 <= w and b3 >= k,                   # 3 палатка
    a1+a2 <= w and b1+b2 >= k,             # 1 и 2
    a1+a3 <= w and b1+b3 >= k,             # 1 и 3
    a2+a3 <= w and b2+b3 >= k,             # 2 и 3
    a1+a2+a3 <= w and b1+b2+b3 >= k        # Все 3 палатки
]


if any(variants):
    print("YES")
else:
    print("NO")