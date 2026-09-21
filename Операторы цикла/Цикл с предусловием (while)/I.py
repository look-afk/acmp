nums = list(map(int, input().split()))

odd_min = min(nums[0::2]) if nums else 0
even_max = max(nums[1::2]) if len(nums) > 1 else 0

print(even_max + odd_min)