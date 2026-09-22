n = int(input())
if n == 0:
    print(0)
else:
    digits = []
    while n > 0:
        n -= 1
        digits.append(str(n % 3 + 1))
        n //= 3
    print(''.join(reversed(digits)))
