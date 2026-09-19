a, b, c = map(int, input().split())
form = ""

if a != 0:
    form = str(a)

if b != 0:
    if b > 0 and form != "":
        form += "+"
    if b == 1:
        form += "x"
    elif b == -1:
        form += "-x"
    else:
        form += f"{b}x"

if c != 0:
    if c > 0 and form != "":
        form += "+"
    if c == 1:
        form += "y"
    elif c == -1:
        form += "-y"
    else:
        form += f"{c}y"

if form == "":
    form = "0"

print(form)
