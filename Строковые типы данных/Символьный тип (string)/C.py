from decimal import Decimal, ROUND_HALF_UP
n = int(input())
e = Decimal('2.7182818284590452353602875')
if n == 0:
    print(int(e.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
else:
    q = e.quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    print(format(q, 'f'))
