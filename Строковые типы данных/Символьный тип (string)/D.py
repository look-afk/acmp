s = input().strip()
if len(s) != 5 or s[2] != '-' or s[0] not in 'ABCDEFGH' or s[3] not in 'ABCDEFGH' or s[1] not in '12345678' or s[4] not in '12345678':
    print('ERROR')
else:
    dx = abs(ord(s[0]) - ord(s[3]))
    dy = abs(int(s[1]) - int(s[4]))
    if {dx, dy} == {1, 2}:
        print('YES')
    else:
        print('NO')
