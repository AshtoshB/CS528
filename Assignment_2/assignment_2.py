from google.cloud import storage
import google.auth


outgoing = {}
incoming = {}
ranks = {}

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
        outgoing[origin].append(ref)
        incoming[ref].append(origin)        
        return


def average():
    total_outgoing = 0
    total_incoming = 0

    for i in range(12000):
        total_outgoing += len(outgoing[i])
        total_incoming += len(incoming[i])

    return {"out": total_outgoing/12000, "in": total_incoming/12000}

def median():
    outgoing_counts = []
    incoming_counts = []
    
    for i in range(12000):
        out_len = len(outgoing[i])
        in_len = len(incoming[i])
        outgoing_counts.append(out_len)
        incoming_counts.append(in_len)

    mid_index = len(outgoing_counts)//2
    outgoing_median = sorted(outgoing_counts)[mid_index]

    mid_index = len(incoming_counts)//2
    incoming_median = sorted(incoming_counts)[mid_index]
    return {"out": outgoing_median, "in": incoming_median}
    
def max():
    outgoign_max = 0
    incoming_max = 0

    for i in range(12000):
        out_len = len(outgoing[i])
        in_len = len(incoming[i])

        if out_len > outgoign_max:
            outgoign_max = out_len

        if in_len > incoming_max:
            incoming_max = in_len

    return {"out": outgoign_max, "in": incoming_max }

def min():
    outgoign_min = float("inf")
    incoming_min = float("inf")

    for i in range(12000): 
        out_len = len(outgoing[i])
        in_len = len(incoming[i])  
        if out_len < outgoign_min:
            outgoign_min = out_len
    
        if in_len < incoming_min:
            incoming_min = in_len

    return {"out": outgoign_min, "in": incoming_min }

def quantiles():
    outs = []
    ins = []

    for i in range(12000):
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

    prev_rank = ranks[x]
    pra =  prev_rank * pra

    return pra 

def page_rank():

    temp_rank = {}
    not_in_threshold = True

    while not_in_threshold:
        not_in_threshold = False

        for i in range(12000):
            new_rank = page_rank_helper(i)
            temp_rank[i] = 0.15/12000 + 0.85 * new_rank

            old_rank = ranks[i]
            change = ((old_rank-new_rank)/old_rank) * 100

            if change > 0.5 or change < -0.5:
                not_in_threshold = True

       
        ranks = temp_rank

def test():
    bucket_name = "assignment2_contents"

    storage_client = storage.Client(project="circular-beacon-508221-d7")
    bucket = storage_client.bucket(bucket_name)

    print("Opening page\n")
    try:
        for i in range(12000):
            page_name = str(i)+".html"
            page = bucket.blob(page_name)
            with page.open("r") as f:
                for line in f:
                    if line[0] == "<":
                        get_link(i, line)

        #print("outgoing:", outgoing)
        #print("incoming:", incoming)
            

                    

    except Exception as e:
        print("error:", e)
        raise


if __name__ == "__main__":
    for i in range(12000):
        outgoing[i] = []
        incoming[i] = []
        ranks[i] = 1

    test()

    averages = average()
    medians = median()
    maxs = max()
    mins = min()
    quant = quantiles()

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