s = input().strip()
print(''.join(chr(ord(c) + 1) if c != 'z' else 'a' for c in s))
