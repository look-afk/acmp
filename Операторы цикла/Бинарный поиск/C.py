left = 1
right = 10**9

while left <= right:
    mid = (left + right) // 2
    print(mid)
    res = input()

    if res == "=":
        break
    elif res == ">":
        left = mid + 1
    elif res == "<":
        right = mid - 1