from main import Chess

a,b = list(map(int,input().split()))
c,d = list(map(int,input().split()))
chess = Chess(a,b)
print(chess.rook(c,d))