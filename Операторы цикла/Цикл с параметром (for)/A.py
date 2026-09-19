l= []
t=input()
for i in range(int(t)):
	l.append(int(input()))
	
if l.count(0) >= l.count(1):
	print(l.count(1))
else:
	print(l.count(0))
	