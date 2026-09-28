from assignment_2 import test

test_case1 = {0: [1], 1:[2], 2:[3], 3:[4], 4:[0]}
test_case2 = {0:[1,2,3,4], 1:[0,2,3,4], 2:[0,1,3,4], 3:[0,1,2,4], 4:[0,1,2,3]}
test_case3 = {0:[1,2,3,4], 1:[0,2], 2:[0], 3:[0,2], 4: []}
test_case4 = {0: [1,2,3,4], 1: [0], 2:[0], 3: [0], 4: [0]}
test_case5 = {0: [], 1: [0], 2: [0, 1], 3: [0, 1, 2], 4: [0, 1, 2, 3],
            5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 5], 7: [0, 1, 2, 3, 4, 5, 6],
            8: [0, 1, 2, 3, 4, 5, 6, 7], 9: [0, 1, 2, 3, 4, 5, 6, 7, 8]}


print("------Test 1--------")
print("Testing with:", test_case1)

# return {"avg": avg, "mid": mid, "quant": quant, "max": mx, "min": mn, "ranking": ranking }
out = test(test_case1)
averages = out["avg"]
mediean = out["mid"]
quantiles = out["quant"]
max = out["max"]
min = out["min"]
ranking = out["ranking"]
ranks = out["ranks"]
closeness = out["closeness"]

if averages["in"] != 1 or averages["out"] != 1:
    print("FAILED averages:", averages)

if mediean["out"] != 1 or mediean["in"] != 1:
    print("FAILED medians:", mediean)

if min["out"] != 1 or min["in"] != 1:
    print("FAILED min:", min)

if max["out"] != 1 or max["in"] != 1:
    print("FAILED max:", max)

if quantiles["out"] != [1, 1, 1, 1, 1] or quantiles["in"] != [1, 1, 1, 1, 1]:
    print("FAILED quantiles:", quantiles)

for page in ranks:
    if abs(ranks[page] - 0.2) > 0.01:
        print("FAILED pagerank page", page, ranks[page])

# every page reaches the others in 1+2+3+4 = 10 clicks -> 4/10 = 0.4
if abs(closeness["score"] - 0.4) > 0.001:
    print("FAILED closeness:", closeness)


print("------Test 2--------")
print("Testing with:", test_case2)

out = test(test_case2)
averages = out["avg"]
mediean = out["mid"]
quantiles = out["quant"]
max = out["max"]
min = out["min"]
ranking = out["ranking"]
ranks = out["ranks"]
closeness = out["closeness"]

if averages["in"] != 4 or averages["out"] != 4:
    print("FAILED averages:", averages)

if mediean["out"] != 4 or mediean["in"] != 4:
    print("FAILED medians:", mediean)

if min["out"] != 4 or min["in"] != 4:
    print("FAILED min:", min)

if max["out"] != 4 or max["in"] != 4:
    print("FAILED max:", max)

if quantiles["out"] != [4, 4, 4, 4, 4] or quantiles["in"] != [4, 4, 4, 4, 4]:
    print("FAILED quantiles:", quantiles)

for page in ranks:
    if abs(ranks[page] - 0.2) > 0.01:
        print("FAILED pagerank page", page, ranks[page])

# every page reaches every other page in 1 click -> 4/4 = 1.0
if abs(closeness["score"] - 1.0) > 0.001:
    print("FAILED closeness:", closeness)


print("------Test 3--------")
print("Testing with:", test_case3)

out = test(test_case3)
averages = out["avg"]
mediean = out["mid"]
quantiles = out["quant"]
max = out["max"]
min = out["min"]
ranking = out["ranking"]
ranks = out["ranks"]
closeness = out["closeness"]

# outgoing: 4,2,1,2,0 -> sorted [0,1,2,2,4]
# incoming: 3,1,3,1,1 -> sorted [1,1,1,3,3]
if abs(averages["in"] - 1.8) > 0.01 or abs(averages["out"] - 1.8) > 0.01:
    print("FAILED averages:", averages)

if mediean["out"] != 2 or mediean["in"] != 1:
    print("FAILED medians:", mediean)

if min["out"] != 0 or min["in"] != 1:
    print("FAILED min:", min)

if max["out"] != 4 or max["in"] != 3:
    print("FAILED max:", max)

if quantiles["out"] != [0, 1, 2, 2, 4] or quantiles["in"] != [1, 1, 1, 3, 3]:
    print("FAILED quantiles:", quantiles)

# page 0 links directly to everyone -> 1.0
if closeness["page"] != 0 or abs(closeness["score"] - 1.0) > 0.001:
    print("FAILED closeness:", closeness)


print("------Test 4--------")
print("Testing with:", test_case4)

out = test(test_case4)
averages = out["avg"]
mediean = out["mid"]
quantiles = out["quant"]
max = out["max"]
min = out["min"]
ranking = out["ranking"]
ranks = out["ranks"]
closeness = out["closeness"]

# outgoing: 4,1,1,1,1   incoming: 4,1,1,1,1
if abs(averages["in"] - 1.6) > 0.01 or abs(averages["out"] - 1.6) > 0.01:
    print("FAILED averages:", averages)

if mediean["out"] != 1 or mediean["in"] != 1:
    print("FAILED medians:", mediean)

if min["out"] != 1 or min["in"] != 1:
    print("FAILED min:", min)

if max["out"] != 4 or max["in"] != 4:
    print("FAILED max:", max)

if quantiles["out"] != [1, 1, 1, 1, 4] or quantiles["in"] != [1, 1, 1, 1, 4]:
    print("FAILED quantiles:", quantiles)

# solved by hand: PR(hub) = 0.03 + 0.85*4*PR(leaf), PR(leaf) = 0.03 + 0.85*PR(hub)/4
if abs(ranks[0] - 0.476) > 0.01:
    print("FAILED pagerank hub:", ranks[0])

for page in [1, 2, 3, 4]:
    if abs(ranks[page] - 0.131) > 0.01:
        print("FAILED pagerank leaf", page, ranks[page])

if ranking[0] != 0:
    print("FAILED top 1 should be page 0:", ranking)

# hub reaches every leaf in 1 click -> 1.0
if closeness["page"] != 0 or abs(closeness["score"] - 1.0) > 0.001:
    print("FAILED closeness:", closeness)


print("------Test 5--------")
print("Testing with:", test_case5)

out = test(test_case5)
averages = out["avg"]
mediean = out["mid"]
quantiles = out["quant"]
max = out["max"]
min = out["min"]
ranking = out["ranking"]
ranks = out["ranks"]
closeness = out["closeness"]

# outgoing: 0..9   incoming: 9..0
if averages["in"] != 4.5 or averages["out"] != 4.5:
    print("FAILED averages:", averages)

if mediean["out"] != 5 or mediean["in"] != 5:      # upper middle of 10 values
    print("FAILED medians:", mediean)

if min["out"] != 0 or min["in"] != 0:
    print("FAILED min:", min)

if max["out"] != 9 or max["in"] != 9:
    print("FAILED max:", max)

if quantiles["out"] != [1, 3, 5, 7, 9] or quantiles["in"] != [1, 3, 5, 7, 9]:
    print("FAILED quantiles:", quantiles)

# page 9 has no incoming links -> 0.15/10 = 0.015
if abs(ranks[9] - 0.015) > 0.001:
    print("FAILED pagerank page 9:", ranks[9])

for place in range(5):
    if ranking[place] != place:
        print("FAILED top 5 should be 0,1,2,3,4:", ranking)
        break

# only page 9 can reach every other page (all in 1 click) -> 1.0
if closeness["page"] != 9 or abs(closeness["score"] - 1.0) > 0.001:
    print("FAILED closeness:", closeness)


print("------Done--------")