from main import Chess
start, finish = input().split()
chess = Chess(start)
print(chess.all(finish))


