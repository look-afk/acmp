import re
s = input().strip()
print('Yes' if re.fullmatch(r'(?:[A-Z][a-z]{1,3})+', s) else 'No')
