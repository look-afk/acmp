x, p, y = map(int, input().split())
 
x *= 100
y *= 100
years = 0
 
while x < y:
    x = x * (100 + p) // 100
    years += 1
 
print(years)