list1=list(map(int, input().split()))
if list1[0] + list1[1] == list1[2]:
    print("YES")
elif list1[1] + list1[2] == list1[0]:
    print("YES")
elif list1[0] + list1[2] == list1[1]:
    print("YES")
else:
    print("NO")