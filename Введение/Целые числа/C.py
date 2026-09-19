def func(a):
    a = str(a)
    if len(a) == 1:
        return 0
    return a[-1]
a = int(input())
print(func(a))