import math

k, m, n = map(int, input().split())
if n <= k:
    ans = 2 * m
else:
    total_sides = 2 * n  
    rounds = math.ceil(total_sides / k) 
    
    ans = rounds * m     

print(ans)

