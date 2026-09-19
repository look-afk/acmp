n = int(input())
total = 0
for i in range(n):
    row = list(map(int, input().split()))
    total += sum(row)
print(total // 2)
