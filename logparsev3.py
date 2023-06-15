# For testing the first 1000 lines:
test_1000 = 1000

# (virtual address region, pmap) : "log details"
superpage_tracker = {}

"""
Input:
- super_va: A string representing the superpage VA region, and is part of the tuple,
  consisting of two strings, that is the related key in the superpage_tracker 
  dictionary which string value will be modified.
- pmap: A string representing the pmap that the VA region is mapped to, and is part of 
  the tuple, consisting of two strings, that is the related key in the superpage_tracker 
  dictionary which string value will be modified.
- operation_words: A string representing the operation words used to check log details.

Effect:
- Modifies the string value in the superpage_tracker dictionary at key super_va to 
  increment the counter for the operation indicated by operation_words.
"""

def add_instance(super_va, pmap, operation_words):
    first_inst = superpage_tracker[(super_va, pmap)].find(operation_words)
    if first_inst != -1:
        x = superpage_tracker[(super_va, pmap)].find("x", first_inst)
        times = int(superpage_tracker[(super_va, pmap)][first_inst+len(operation_words)+1: x])
        superpage_tracker[(super_va, pmap)] = superpage_tracker[(super_va, pmap)][0:first_inst+len(operation_words)+1]\
            + str(times+1) + superpage_tracker[(super_va, pmap)][x:]
        return 0
    else: 
        return -1


"""
Objective:
- Given a trace log file tracking superpage creations, identify how often a virtual address region
    fails/succeeds in being promoted to a superpage.
Input:
- ktr.out.txt: A trace file of which the 2+ lines log, in order, memory operations. Each line follows a format of:
    
[index of the operation’s execution] [operation]: [optional details] pmap [hex address of physical memory mapping]
    
- There are four operations: pmap_remove_pages, pmap_promote_pde, pmap_enter_pde, pmap_demote_pde.
- [optional details] only applies to pmap_promote_pde, pmap_enter_pde, pmap_demote_pde. Listed are 
    the formats for [optional details]:
    - pmap_enter_pde: success for va [hex virtual address] in
    - pmap_demote_pde: [success/failure] for va [hex virtual address] in
    - pmap_promote_pde: [success/failure/protect] for va [hex virtual address] in

Output:
- A log keeping track, for each superpage virtual address region, the number of times protection
    was added, a superpage was promoted, or a superpage was entered. The log also notes when a 
    superpage promotion failed or succeeded.

Special Edge Conditions:
- 

Examples:
    - We failed to promote 7 times, and then succeeded.
    - 1254-1256, there was protect, fail and ultimately succeed
    - This is the page we removed, which is part of a larger superpage that we failed 6x and succeeded.
    - We have 25 regions we failed no times before succeeded.
    - No times before succeeded, multiple times before succeeded, multiple times before failed to promote
    - Promote and then demote and then repromoted
    
    27 pmap_remove_pages: pmap 0xfffffe0185998540
    28 pmap_promote_pde: success for va 0x3c8000 in pmap 0xfffffe0185998540
   940 pmap_promote_pde: failure for va 0x80a1cd000 in pmap 0xfffffe018598cd60
  1058 pmap_promote_pde: protect for va 0x80946e000 in pmap 0xfffffe018598cd60
  1274 pmap_enter_pde: success for va 0x200000 in pmap 0xfffffe010cfeb788
  1202 pmap_demote_pde: success for va 0x808098000 in pmap 0xfffffe010cfeb788
394596 pmap_demote_pde: failure for va 0x8101ff000 in pmap 0xfffffe01a4752170
"""

with open("ktr.out.txt") as f:
    while True:
        for line in f:
            # Get index.
            idx = line[0:7].strip(" ")
            
            # Get the operation.
            space_idx = line.find(" ", 7, 26)
            operation = line[7: space_idx-1]
            # print("\"", operation, "\"", sep="")
            
            if operation == "pmap_enter_pde" or operation == "pmap_demote_pde" or operation == "pmap_promote_pde":
                # Get the virtual address.
                va_idx = line.find("va ")
                va_end = line.find(" ", va_idx+3)
                va = line[va_idx+3: va_end]
                # print("\"", va, "\"", sep="")
                
                # Get the 2MB-aligned superpage VA region.
                super_va = va[:len(va)-6]
                last_num = va[len(va)-6: len(va)-5]
                if last_num == "a" or last_num == "c" or last_num == "e":
                    super_va += last_num
                elif last_num == "b":
                    super_va += "a"
                elif last_num == "d":
                    super_va += "c"
                elif last_num == "f":
                    super_va += "e"
                else:
                    super_va += str(int(int(last_num) / 2) * 2)
                super_va += "00000"
                # print(idx, " \"", super_va, "\"", sep="")
                
                # Get the pmap.
                pmap_index = line.find("pmap", 11)
                pmap = line[pmap_index+5:]
                pmap = pmap[0: len(pmap)-1]
                # print("pmap:", pmap)
                
                # Check if superpage VA region in dictionary.
                if (super_va, pmap) not in superpage_tracker:
                    superpage_tracker[(super_va, pmap)] = ""
                    
                # Check if protection was added.
                if line.find("protect") != -1:
                    # Find first instance of "Protection added". If it exists, add to the counter. Otherwise, start count from 1.
                    if add_instance(super_va, pmap, "Protection added") == -1:
                        superpage_tracker[(super_va, pmap)] += "Protection added 1x. "
                    
                # Check if operation was successful.
                elif line.find("success") != -1:
                    
                    # Check if operation was entering superpage, promotion, or demotion.
                    if operation == "pmap_enter_pde":
                        if add_instance(super_va, pmap, "entered") == -1:
                            superpage_tracker[(super_va, pmap)] += "Superpage entered 1x. "
                    
                    elif operation == "pmap_promote_pde":
                        if add_instance(super_va, pmap, "promoted") == -1:
                            superpage_tracker[(super_va, pmap)] += "Superpage promoted 1x. "
                    
                    elif operation == "pmap_demote_pde":
                        if add_instance(super_va, pmap, "demoted") == -1:
                            superpage_tracker[(super_va, pmap)] += "Superpage demoted 1x. "
                
                # Check if operation was failure.
                elif line.find("failure") != -1:
                    
                    # Check if operation was promotion or demotion.   
                    if operation == "pmap_promote_pde":
                        if add_instance(super_va, pmap, "promotion failed") == -1:          
                            superpage_tracker[(super_va, pmap)] += "Superpage promotion failed 1x. "
                    
                    elif operation == "pmap_demote_pde":
                        if add_instance(super_va, pmap, "demotion failed") == -1:
                            superpage_tracker[(super_va, pmap)] += "Superpage demotion failed 1x. "
                
            # Testing:
            # test_1000 -= 1
            # if test_1000 < 0:
            #     for tup, log in superpage_tracker.items():
            #         print(tup[0], ": ", log, sep="") 
            #         # print(tup[0], ", ", tup[1], ": ", log, sep="") 
            #         # print("VA: ", tup[0], ", pmap: ", tup[1], ": ", log, sep="") 
            #     # print(superpage_tracker)
            #     exit()
        for tup, log in superpage_tracker.items():
            # print(tup[0], "", ": ", log, sep="") 
            print(tup[0], ", ", tup[1], ": ", log, sep="") 
        exit()