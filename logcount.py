# For testing the first 1000 lines:
test_1000 = 1000

"""
    Global dictionary tracking all pmaps and VA regions.
"""
# {pmap : {va region: [promotion failures, protections added]}}
pmap_tracker = {}

"""
    Dictionaries tracking superpage creations.
"""
# {# of promotion fails before promotion : # of occurrences}
promotion_fails_success = {}

# {# of promotion fails before pmap removal : # of occurrences}
promotion_fails_no_success = {}

# {# of promotion fails before entering : # of occurrences}
enter_fails_success = {}


"""
    Dictionaries tracking added protections.
"""
# {# of protections added before promotion : # of occurrences}
promotion_protect_success = {}

# {# of protections added before pmap removal : # of occurrences}
promotion_protect_no_success = {}

# {# of protections added before entering : # of occurrences}
enter_protect_success = {}

# global demotion counter
demotions = 0

"""
Objective:
- Given a trace log file tracking superpage creations, identify how often a virtual address region
    fails in being promoted/entered to a superpage before success, if any.
- Count the total amount of demotions logged.
- Count the number of protections that did/didn't lead to promotion before pmap_remove_pages is called.

Input:
- ktr.out.txt: A trace file of which the 2+ lines log, in order, memory operations. Each line follows a format of:
    
[index of the operation’s execution] [operation]: [optional details] pmap [hex address of physical memory mapping]
    
- There are four operations: pmap_remove_pages, pmap_promote_pde, pmap_enter_pde, pmap_demote_pde.
- [optional details] only applies to pmap_promote_pde, pmap_enter_pde, pmap_demote_pde. Listed are 
    the formats for [optional details]:
    - pmap_enter_pde: success for va [hex virtual address] in
    - pmap_demote_pde: [success/failure] for va [hex virtual address] in
    - pmap_promote_pde: [success/failure/protect] for va [hex virtual address] in

- Examples of inputs:
    27 pmap_remove_pages: pmap 0xfffffe0185998540
    28 pmap_promote_pde: success for va 0x3c8000 in pmap 0xfffffe0185998540
   940 pmap_promote_pde: failure for va 0x80a1cd000 in pmap 0xfffffe018598cd60
  1058 pmap_promote_pde: protect for va 0x80946e000 in pmap 0xfffffe018598cd60
  1274 pmap_enter_pde: success for va 0x200000 in pmap 0xfffffe010cfeb788
  1202 pmap_demote_pde: success for va 0x808098000 in pmap 0xfffffe010cfeb788
394596 pmap_demote_pde: failure for va 0x8101ff000 in pmap 0xfffffe01a4752170

Output:
- A log counting the number of times a superpage VA region failed 0 times before promotion,
  failed 1 time before promotion, etc. Also, counting how often promotion failures occur before
  a superpage entering occurs ie 0 failures before entering, 1 failure before entering, etc. 
  Also, failed 0 times before pmap removal (without promotion),
  failed 1 time before pmap removal (without promotion), etc.
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
            
            # Get the pmap.
            pmap_index = line.find("pmap", 11)
            pmap = line[pmap_index+5:]
            pmap = pmap[0: len(pmap)-1]
            # print("pmap:", pmap)
            
            # Check if pmap in dictionary.
            if pmap not in pmap_tracker:
                pmap_tracker[pmap] = {}
            
            if operation.find("pmap") != -1 and operation != "pmap_remove_pages":
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
                    
                # Check if superpage VA is in the nested dictionary at key pmap.
                if super_va not in pmap_tracker[pmap]:
                    pmap_tracker[pmap][super_va] = [0, 0]
                
                if operation == "pmap_promote_pde":
                    # If there's a failure to promote, increment fail counter.
                    if line.find("failure") != -1:
                        pmap_tracker[pmap][super_va][0] += 1
                    # If a protection is added, increment the protection counter.
                    elif line.find("protect") != -1:
                        pmap_tracker[pmap][super_va][1] += 1
                    # Else, increment counts and delete the superpage VA from mapping.
                    else:
                        # Increment promotion fail count for success.
                        if pmap_tracker[pmap][super_va][0] not in promotion_fails_success:
                            promotion_fails_success[pmap_tracker[pmap][super_va][0]] = 1
                        else:
                            promotion_fails_success[pmap_tracker[pmap][super_va][0]] += 1
                            
                        # Increment protect added count for success.
                        if pmap_tracker[pmap][super_va][1] not in promotion_protect_success:
                            promotion_protect_success[pmap_tracker[pmap][super_va][1]] = 1
                        else:
                            promotion_protect_success[pmap_tracker[pmap][super_va][1]] += 1
                            
                        del pmap_tracker[pmap][super_va]
                
                elif operation == "pmap_enter_pde":
                    # Increment enter fail count for no success.
                    if pmap_tracker[pmap][super_va][0] not in enter_fails_success:
                        enter_fails_success[pmap_tracker[pmap][super_va][0]] = 1
                    else:
                        enter_fails_success[pmap_tracker[pmap][super_va][0]] += 1
                        
                    # Increment protect added count for no success.
                    if pmap_tracker[pmap][super_va][1] not in enter_protect_success:
                        enter_protect_success[pmap_tracker[pmap][super_va][1]] = 1
                    else:
                        enter_protect_success[pmap_tracker[pmap][super_va][1]] += 1
                        
                    del pmap_tracker[pmap][super_va]
                        
                elif operation == "pmap_demote_pde":
                    demotions += 1
                    
            
            # The operation is "pmap_remove_pages".
            else:
                # Iterate through pmap_tracker for pmap, and count up.
                for super_va, counts in pmap_tracker[pmap].items():
                    # Increment the fail count in the no success dictionary.
                    if counts[0] not in promotion_fails_no_success:
                        promotion_fails_no_success[counts[0]] = 1
                    else:
                        promotion_fails_no_success[counts[0]] += 1
                        
                    # Increment the protect count in the no success dictionary.
                    if counts[1] not in promotion_protect_no_success:
                        promotion_protect_no_success[counts[1]] = 1
                    else:
                        promotion_protect_no_success[counts[1]] += 1
                
                # Remove pmap from pmap_tracker.
                del pmap_tracker[pmap]
                
            # Testing:
            # test_1000 -= 1
            # if test_1000 < 0:
                # for spage, log in pmap_tracker.items():
                #     print(spage, ": ", log, sep="") 
                # print(pmap_tracker)
                # for num_fails, occurrences in promotion_fails_success.items():
                #     print("Promotions after ", num_fails, " failures: ", occurrences, sep = "")
                # for num_fails, occurrences in promotion_fails_no_success.items():
                #     print(num_fails, " failures before page removal (no successful promotion): ", occurrences, sep = "")
                # exit()
        # for spage, log in pmap_tracker.items():
        #     print(spage, ": ", log, sep="") 
        
        
        
        # Sort the dictionaries.
    
        """
            Dictionaries tracking superpage creations.
        """
        succ_keys = list(promotion_fails_success.keys())
        succ_keys.sort()
        sorted_promotion_fails_success = {i: promotion_fails_success[i] for i in succ_keys}
        
        no_succ_keys = list(promotion_fails_no_success.keys())
        no_succ_keys.sort()
        sorted_promotion_fails_no_success = {i: promotion_fails_no_success[i] for i in no_succ_keys}
        
        succ_enter_keys = list(enter_fails_success.keys())
        succ_enter_keys.sort()
        sorted_enter_fails_success = {i: enter_fails_success[i] for i in succ_enter_keys}
        
        """
            Dictionaries tracking added protections.
        """
        succ_keys = list(promotion_protect_success.keys())
        succ_keys.sort()
        sorted_promotion_protect_success = {i: promotion_protect_success[i] for i in succ_keys}
        
        no_succ_keys = list(promotion_protect_no_success.keys())
        no_succ_keys.sort()
        sorted_promotion_protect_no_success = {i: promotion_protect_no_success[i] for i in no_succ_keys}
        
        succ_enter_keys = list(enter_protect_success.keys())
        succ_enter_keys.sort()
        sorted_enter_protect_success = {i: enter_protect_success[i] for i in succ_enter_keys}
        
        
        # Print the sorted dictionaries.
        
        """
            FAILURES:
        """
        print("\n      ------FAILURES------       \n")
        # Print the counts of failures before superpage promotion.
        print("Counting failures before superpage promotion:\n")
        for num_fails, occurrences in sorted_promotion_fails_success.items():
            print("Promotions after ", num_fails, " failures: ", occurrences, sep = "")
            
        # Print the counts of failures before superpage entering.
        print("\nCounting failures before superpage entering:\n")
        for num_fails, occurrences in sorted_enter_fails_success.items():
            print("Entering after ", num_fails, " failures: ", occurrences, sep = "")
            
        # Print the counts of failures without superpage creation.
        print("\nFailures to create superpage creations without success:\n")
        for num_fails, occurrences in sorted_promotion_fails_no_success.items():
            if num_fails == 0:
                continue
            print(num_fails, " failures before pmap_remove_pages (no successful promotion): ", occurrences, sep = "")
            
        """
            PROTECTIONS:
        """
        print("\n      ------PROTECTIONS------       \n")
        # Print the counts of added protections before superpage promotion.
        print("\nCounting protections before superpage promotion:\n")
        for num_fails, occurrences in sorted_promotion_protect_success.items():
            print("Promotions after ", num_fails, " protections: ", occurrences, sep = "")
            
        # Print the counts of added protections before superpage entering.
        print("\nCounting protections before superpage entering:\n")
        for num_fails, occurrences in sorted_enter_protect_success.items():
            print("Entering after ", num_fails, " protections: ", occurrences, sep = "")
            
        # Print the counts of added protections without superpage creation.
        print("\nProtections to create superpage creations without success:\n")
        for num_fails, occurrences in sorted_promotion_protect_no_success.items():
            if num_fails == 0:
                continue
            print(num_fails, " protections before pmap_remove_pages (no successful promotion): ", occurrences, sep = "")
        
        print("\nTotal demotions:", demotions)
        exit()