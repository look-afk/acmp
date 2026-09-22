k = int(input())
p = ['G','C','V']
for _ in range(k):
    p[1], p[2] = p[2], p[1]
    p[0], p[1] = p[1], p[0]
print(''.join(p))
