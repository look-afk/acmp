s = input().strip()
ok = len(s) >= 12 and any(c.islower() for c in s) and any(c.isupper() for c in s) and any(c.isdigit() for c in s)
print('Yes' if ok else 'No')
