n = int(input())
if n == 0:
    print(0)
else:
    digits = []
    while n != 0:
        r = n % 3
        n = -(n - r) // 3
        digits.append(str(r))
    print(''.join(reversed(digits)))
