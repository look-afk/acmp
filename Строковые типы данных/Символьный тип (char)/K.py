n = int(input())
a, b, c = map(int, input().split())
pool = {'U': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'L': 'abcdefghijklmnopqrstuvwxyz', 'D': '0123456789'}
need = {'U': a, 'L': b, 'D': c}
flex = n - a - b - c
out = []
last = None
while len(out) < n:
    ch = None
    req = [t for t in 'ULD' if need[t] > 0]
    order = sorted(req, key=lambda t: -need[t]) if req else list('ULD')
    for t in order:
        for c in pool[t]:
            if c != last:
                if need[t] > 0:
                    need[t] -= 1
                    ch = c
                    break
                if flex > 0:
                    flex -= 1
                    ch = c
                    break
        if ch:
            break
    if not ch:
        for t in 'ULD':
            for c in pool[t]:
                if c != last:
                    ch = c
                    break
            if ch:
                break
    out.append(ch)
    last = ch
print(''.join(out))
