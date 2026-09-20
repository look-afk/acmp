numbers = map(int, input().split())

previous = None
direction = 0
current_length = 0
maximum_length = 0

for number in numbers:
	if number == 0:
		break

	if previous is None:
		current_length = 1
	elif number > previous:
		if direction == 1:
			current_length += 1
		else:
			current_length = 2
		direction = 1
	elif number < previous:
		if direction == -1:
			current_length += 1
		else:
			current_length = 2
		direction = -1
	else:
		current_length = 1
		direction = 0

	maximum_length = max(maximum_length, current_length)
	previous = number

print(maximum_length)
