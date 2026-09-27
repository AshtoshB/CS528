from assignment_2 import test 

test_case1 = {0: [1], 1:[2], 2:[3], 3:[4], 4:[0]}



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

if averages["in"] != 1 or averages["out"] != 1:
    print("FAILED averages:", averages)

if mediean["out"] !=1 or mediean["in"] != 1:
    print("FAILED medians:", mediean)

if min["out"] != 1 or min["in"] != 1:
    print("FAILED min:", out["min"])

if max["out"] != 1 or max["in"] != 1:
    print("FAILED max:", out["max"])

if quantiles["out"] != [1, 1, 1, 1, 1] or quantiles["in"] != [1, 1, 1, 1, 1]:
    print("FAILED quantiles:", out["quant"])

for page in ranking:
    if abs(ranks[page] - 0.2) > 0.01:
        print("FAILED pagerank page", page, ranking[page])

print(ranks)
