s = input().strip()
vals = {**{str(d): d for d in range(10)}, **{chr(ord('A') + i): 10 + i for i in range(26)}}
if not s or any(ch not in vals for ch in s):
    print(-1)
else:
    m = max(vals[ch] for ch in s)
    print(max(2, m + 1))
