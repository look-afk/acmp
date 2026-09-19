list1 = list(map(int, input().split()))
condition0 = list1[0] >= list1[1] and list1[0] > list1[2]
condition3 = list1[1]+list1[2] <= list1[0]
if condition0 and condition3:
    print("YES")
else:
    print("NO")