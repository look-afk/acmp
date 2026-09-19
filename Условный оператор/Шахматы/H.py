from main import Chess

a,b,c,d = list(map(int,input().split()))
chess = Chess(a,b)
print(chess.board(a,b,c,d))