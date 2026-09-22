n = int(input())
for _ in range(n):
    s = input().strip()
    print('Yes' if int(s, 2) % 7 == 0 else 'No')
