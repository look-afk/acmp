s = input().strip()
V = set('aeiouy')
t = [c in V for c in s]
# find runs longer than 2 of same type; need insertions to break them
# for a run of length L of same type, need floor((L-1)/2) insertions of opposite type? 
# actually inserting one opposite char splits; min inserts for run L is (L-1)//2? 
# run of 3 needs 1 insert; run of 5 needs inserts after pos 2,4 -> 2; so (L-1)//2? L=3->1, L=4->2? 
# wait max allowed 2 consecutive, so need to break into pieces of len<=2
# min inserts = ceil(L/2)-1? L=3 ceil1.5-1=1; L=4 ceil2-1=1 but 4 needs 1 insert -> 2+2 ok; L=5 needs 2 inserts
# so inserts = (L-1)//2? L=3:1 L=4:1 L=5:2. Yes.
ans = 0
i = 0
while i < len(s):
    j = i
    while j < len(s) and t[j] == t[i]:
        j += 1
    L = j - i
    if L > 2:
        ans += (L - 1) // 2
    i = j
print(ans)
