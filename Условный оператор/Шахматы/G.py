from main import Chess
chess = Chess(2,3)
c,d = list(map(str,input().strip()))
c = (ord(c) - ord('A') + 1)
print(chess.square(c,d))