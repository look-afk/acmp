def func():
    k, n = map(int, input().split())
    page = (n - 1) // k + 1
    line = (n - 1) % k + 1
    
    print(page, line)

func()