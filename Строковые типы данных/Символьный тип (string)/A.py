c = input().strip()
s = 'qwertyuiopasdfghjklzxcvbnm'
print(s[(s.index(c) + 1) % len(s)])
