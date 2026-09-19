def func(a):
    how_many = a//2
    if a/2 != how_many:
        how_many += 1
    
    print(how_many**2)

a = int(input())
func(a)