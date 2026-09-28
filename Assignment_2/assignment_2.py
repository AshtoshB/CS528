from google.cloud import storage
import time

outgoing = {}
incoming = {}
ranks = {}

def initiate(origin=None, ref=None, n=12000, fill = False):
    if fill:
        outgoing.clear()
        incoming.clear()
        ranks.clear()

        for i in range(n):
            outgoing[i] = []
            incoming[i] = []
            ranks[i] = 1 
        
    if origin != None and ref != None:
        outgoing[origin].append(ref)
        incoming[ref].append(origin)

    


def get_link(origin, code):
    #print("here")    
    if len(code) < 7:
        return 
    
    href_command = code[3] + code[4] + code[5] + code[6]
    if href_command == "HREF":
        ref_begin = 9
        ref = ""
        for i in range(ref_begin, len(code)):
            if code[i] == ".":
                break

            ref += code[i]

        ref = int(ref)
        initiate(origin=origin, ref=ref) 
        return


def average(n= 12000):
    total_outgoing = 0
    total_incoming = 0

    for i in range(n):
        total_outgoing += len(outgoing[i])
        total_incoming += len(incoming[i])

    return {"out": total_outgoing/n, "in": total_incoming/n}

def median(n=12000):
    outgoing_counts = []
    incoming_counts = []
    
    for i in range(n):
        out_len = len(outgoing[i])
        in_len = len(incoming[i])
        outgoing_counts.append(out_len)
        incoming_counts.append(in_len)

    mid_index = len(outgoing_counts)//2
    outgoing_median = sorted(outgoing_counts)[mid_index]

    mid_index = len(incoming_counts)//2
    incoming_median = sorted(incoming_counts)[mid_index]
    return {"out": outgoing_median, "in": incoming_median}
    
def max(n=12000):
    outgoign_max = 0
    incoming_max = 0

    for i in range(n):
        out_len = len(outgoing[i])
        in_len = len(incoming[i])

        if out_len > outgoign_max:
            outgoign_max = out_len

        if in_len > incoming_max:
            incoming_max = in_len

    return {"out": outgoign_max, "in": incoming_max }

def min(n=12000):
    outgoign_min = float("inf")
    incoming_min = float("inf")

    for i in range(n): 
        out_len = len(outgoing[i])
        in_len = len(incoming[i])  
        if out_len < outgoign_min:
            outgoign_min = out_len
    
        if in_len < incoming_min:
            incoming_min = in_len

    return {"out": outgoign_min, "in": incoming_min }

def quantiles(n=12000):
    outs = []
    ins = []

    for i in range(n):
        out_len = len(outgoing[i])
        in_len = len(incoming[i])  
       
        outs.append(out_len)
        ins.append(in_len)

    outs.sort()
    ins.sort()

    out_div = (len(outs)//5)
    q1_out = outs[out_div - 1]
    q2_out = outs[(out_div * 2) -1]
    q3_out = outs[(out_div * 3) -1]
    q4_out = outs[(out_div * 4) -1]
    q5_out = outs[(out_div * 5) -1]

    in_div = (len(ins)//5)
    q1_in = ins[in_div -1]
    q2_in = ins[(in_div * 2) -1]
    q3_in = ins[(in_div * 3) -1]
    q4_in = ins[(in_div * 4)-1]
    q5_in = ins[(in_div * 5)-1]

    return {"out": [q1_out, q2_out, q3_out, q4_out, q5_out], "in": [q1_in, q2_in, q3_in, q4_in, q5_in]}



def page_rank_helper(x):

    PR = incoming[x]

    pra = 0
    for T in PR:
        CT = outgoing[T]
        pra += ranks[T]/len(CT)

    return pra 

def page_rank(n=12000):

    
    not_in_threshold = True

    while not_in_threshold:
        not_in_threshold = False

        temp_rank = {}
        for i in range(n):
            new_rank = 0.15/n + 0.85 * page_rank_helper(i)
            temp_rank[i] = new_rank

            old_rank = ranks[i]
            change = ((old_rank-new_rank)/old_rank) * 100

            if change > 0.5 or change < -0.5:
                not_in_threshold = True

       
        ranks.update(temp_rank)

   


def page_rank_top_5():
    ranked = {}

    for i in range(5):
        ranked[i] = -1

    for rank in ranks:

        for i in range(5):
            curr_rank = ranked[i]

            if curr_rank ==  - 1:
                ranked[i] = rank
                break 

            curr_rank_value = ranks[curr_rank]

            if ranks[rank] > curr_rank_value:
                ranked[i] = rank
                if i < 4:
                    for j in range(i+1, 5):
                        temp = ranked[j]
                        ranked[j] = curr_rank
                        curr_rank = temp

                break

    return ranked


def bfs(start, n):
    dist = {start: 0}
    q = [start]
    head = 0

    while head < len(q):
        u = q[head]
        head += 1

        for v in outgoing[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)

        if len(dist) == n:
            break

    return dist


def page_centrality(n=12000):
    best_page = -1
    best_score = -1

    for page in range(n):
        dist = bfs(page, n)
        
        score = 0

        if len(dist) >= n:
            total = 0
            for other in dist:
                total += dist[other]

            score = (n-1)/total

        if score > best_score:
            best_score = score 
            best_page = page

    return {"page": best_page, "score": best_score} 


def cloud_initiate():
    bucket_name = "assignment2_contents"

    storage_client = storage.Client(project="circular-beacon-508221-d7")
    bucket = storage_client.bucket(bucket_name)

    print("Opening page\n")
    try:
        for i in range(12000):
            page_name = str(i)+".html"
            page = bucket.blob(page_name)
            #print("page", page_name)
            with page.open("r") as f:
                for line in f:
                    if line[0] == "<":
                        get_link(i, line)

        #print("outgoing:", outgoing)
        #print("incoming:", incoming)
            

                    

    except Exception as e:
        print("error:", e)
        raise


def test(outgoing):
    n = len(outgoing)
    initiate(n=n, fill=True)

    for origin in outgoing:
        for ref in outgoing[origin]:
            initiate(origin=origin, ref=ref)
    
    avg = average(n)
    mid = median(n)
    quant = quantiles(n)
    mx = max(n)
    mn = min(n)
    page_rank(n)
    ranking = page_rank_top_5()
    closeness = page_centrality(n)

    return {"avg": avg, "mid": mid, "quant": quant, "max": mx, "min": mn, "ranking": ranking, "ranks": ranks, "closeness": closeness }

if __name__ == "__main__":

    initiate(fill=True)

    real_start = time.time()
    
    cloud_initiate()

    time_taken = time.time() - real_start
    print ("Getting files and getting the incoming and outgoing links took:", time_taken, "seconds")

    start = time.time()
    averages = average()
    medians = median()
    maxs = max()
    mins = min()
    quant = quantiles()
    
    print ("Calculating took:", time.time() - start, "seconds")
    
    print("Outgoing average:", averages["out"])
    print("Incoming average:", averages["in"])
    print("Ougoing median:", medians["out"])
    print("Incoming median:", medians["in"])
    print("Outgoing max:", maxs["out"])
    print("Incoming max:", maxs["in"])
    print("Outgoing min:", mins["out"])
    print("Incoming min:", mins["in"])
    print("Outgoing quantiles:", quant["out"])
    print("Incmoing quantiles:", quant["in"])

    start = time.time()
    page_rank()
    print ("PageRank took:", time.time() - start, "seconds")
    
    ranking = page_rank_top_5()


    for rank in ranking:
        true_rank = rank + 1
        page = ranking[rank]
        score = ranks[page]
        print("PageRank", true_rank, "is:", page, "    With score:", score)


    start = time.time()
    best_centrality = page_centrality()

    print("Closness took", time.time() - start, "seconds")
    print("Best closness centrality page:", best_centrality["page"], "  With score:", best_centrality["score"])

    print("Total time:", time.time()-real_start, "seconds")