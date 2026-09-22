m = int(input())
b = bin(m)[2:]
print(int(b[::-1], 2))
