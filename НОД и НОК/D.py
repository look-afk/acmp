import math

# Считываем номера i и j
i, j = map(int, input().split())

# 1. Находим НОД индексов
g = math.gcd(i, j)

# 2. Находим F_g по модулю 10^9
MOD = 10**9

a, b = 0, 1
for _ in range(g):
    a, b = b, (a + b) % MOD

# В переменной 'a' окажется F_g
print(a)