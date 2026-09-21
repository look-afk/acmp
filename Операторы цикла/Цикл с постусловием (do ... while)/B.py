l = list(map(int,input().split()))
n=[]
for i in l:
	if i ==0:
		break
	else:
		n.append(i)
print(sum(n))