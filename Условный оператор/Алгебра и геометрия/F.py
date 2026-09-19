a = sorted(list(map(int, input().split())))
b = sorted(list(map(int, input().split())))

if a == b:
    print("Boxes are equal")
elif a[0] <= b[0] and a[1] <= b[1] and a[2] <= b[2]:
    print("The first box is smaller than the second one")
elif a[0] >= b[0] and a[1] >= b[1] and a[2] >= b[2]:
    print("The first box is larger than the second one")
else:
    print("Boxes are incomparable")