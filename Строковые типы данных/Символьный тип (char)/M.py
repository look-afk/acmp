s = input().strip()
parts = s.split('.')
ok = len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
print('Good' if ok else 'Bad')
