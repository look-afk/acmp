s = input().strip()
cnt = 0
for i in range(len(s) - 4):
    w = s[i:i+5]
    if w == '>>-->' or w == '<--<<':
        cnt += 1
print(cnt)
