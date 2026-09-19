from tkinter import Y


class Chess:
    def __init__(self, x, y=None):
        if y is None:
            self.x, self.y = self.coord(x)
        else:
            self.x, self.y = int(x), int(y)

    @staticmethod
    def coord(cell):
        cell = "".join(ch for ch in str(cell).strip().upper() if ch.isalnum())
        x = ord(cell[0]) - ord("A") + 1
        y = int(cell[1:])
        return x, y

    def rook(self, new_x, new_y):
        return "YES" if (self.x == new_x or self.y == new_y) else "NO"

    def king(self, new_x, new_y):
        return "YES" if max(abs(self.x - new_x), abs(self.y - new_y)) == 1 else "NO"

    def queen(self, new_x, new_y):
        return "YES" if (self.rook(new_x, new_y) == "YES" or self.bishop(new_x, new_y) == "YES") else "NO"

    def bishop(self, new_x, new_y):
        return "YES" if abs(self.x - new_x) == abs(self.y - new_y) else "NO"

    def knight(self, new_x, new_y):
        dx, dy = abs(self.x - new_x), abs(self.y - new_y)
        return "YES" if (dx == 2 and dy == 1) or (dx == 1 and dy == 2) else "NO"

    def pawn(self, new_x, new_y):
        bigmove = False
        if self.y == 1:
            return "NO"
        if self.y == 2:
            bigmove = True
        if self.y + 1 == new_y and self.x == new_x:
            return "YES"
        elif bigmove:
            if self.y + 2 == new_y and self.x == new_x:
                return "YES"
        return "NO"
    def square(self,m1,m2):
        A,B = int(m1),int(m2)
        if A%2 ==0:
            if B%2 == 0:
                return "BLACK"
            else:
                return "WHITE"
        else:
            if B%2 == 0:
                return "WHITE"
            else:
                return "BLACK"
    def board(self,m1,m2,t1,t2):
        if self.square(m1,m2) == self.square(t1,t2):
            return("YES")
        else:
            return("NO")

    def all(self, new_x, new_y=None):
        if new_y is None:
            new_x, new_y = self.coord(new_x)
        else:
            new_x, new_y = int(new_x), int(new_y)

        pieces = [
            ("King", self.king(new_x, new_y)),
            ("Queen", self.queen(new_x, new_y)),
            ("Rook", self.rook(new_x, new_y)),
            ("Bishop", self.bishop(new_x, new_y)),
            ("Knight", self.knight(new_x, new_y)),
            ("Pawn", self.pawn(new_x, new_y)),
        ]
        can_move = [name for name, answer in pieces if answer == "YES"]
        return "\n".join(can_move) if can_move else "Nobody"
