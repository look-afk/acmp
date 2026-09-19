from math import sqrt

S, P = map(int, input().split())

D = S * S - 4 * P

if D < 0:
    print("NO")
else:
    if D >= 0 and int(sqrt(D)) ** 2 == D:
        x = (S - sqrt(D)) / 2
        y = (S + sqrt(D)) / 2

        if x.is_integer() and y.is_integer():
            print(int(x), int(y))
        else:
            print("NO")
    else:
        print("NO")
