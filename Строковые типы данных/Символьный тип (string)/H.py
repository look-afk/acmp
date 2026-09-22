msg = input().strip()
word = input().strip()
def dec(s, k):
    return ''.join(chr((ord(c) - 65 - k) % 26 + 65) for c in s)
for k in range(26):
    d = dec(msg, k)
    if word in d:
        print(d)
        break
else:
    print('IMPOSSIBLE')
