state = tuple(input() for _ in range(3))
next_state = {
    ("black", "black", "green"): ("black", "black", "GREEN"),
    ("black", "black", "GREEN"): ("black", "yellow", "black"),
    ("black", "yellow", "black"): ("red", "black", "black"),
    ("red", "black", "black"): ("red", "yellow", "black"),
    ("red", "yellow", "black"): ("black", "black", "green"),
    ("black", "YELLOW", "black"): ("black", "YELLOW", "black"),
}

if state in next_state:
    print(*next_state[state], sep="\n")
else:
    print("error")
