def func():
    n = int(input())
    fives = n // 5
    remainder = n % 5
    
    if remainder == 0:
        threes = 0
    elif remainder == 1:
        fives -= 1
        threes = 2
    elif remainder == 2:
        fives -= 2
        threes = 4
    elif remainder == 3:
        threes = 1
    elif remainder == 4:
        fives -= 1
        threes = 3
    print(fives,threes)
func()