s = input().strip()
h = {'0': 1, '6': 1, '8': 2, '9': 1}
print(sum(h.get(c, 0) for c in s))
