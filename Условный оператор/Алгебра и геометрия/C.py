from math import sqrt
list1 = list(map(int,input().split()))

x1 = list1[0]
y1 = list1[1]
x2 = list1[2]
y2 = list1[3]

a = pow((x1 - x2),2)
b = pow((y1 - y2),2)
c_pow = a+b
c = sqrt(c_pow)
print(c)