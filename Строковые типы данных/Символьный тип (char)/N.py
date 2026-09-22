eq = input().strip()
pos = [eq[0], eq[2], eq[4]]
op = eq[1]
x = None
d = [None, None, None]
for i, ch in enumerate(pos):
    if ch == 'x':
        x = i
    else:
        d[i] = int(ch)
if x == 0:
    r = d[2] - d[1] if op == '+' else d[2] + d[1]
elif x == 1:
    r = d[2] - d[0] if op == '+' else d[0] - d[2]
else:
    r = d[0] + d[1] if op == '+' else d[0] - d[1]
print(r)
