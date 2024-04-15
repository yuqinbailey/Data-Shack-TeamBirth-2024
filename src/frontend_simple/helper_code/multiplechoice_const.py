
ANSWER_LISTS = [
    ["Completely Agree", "Strongly Agree", "Somewhat Agree", "Somewhat Disagree", 
     "Strongly Disagree", "Completely Disagree", "Prefer Not to Answer"],

     ["Strongly Agree", "Agree", "Somewhat Agree", "Somewhat Disagree",
    "Disagree", "Strongly Disagree", "Prefer Not to Answer"],
    
    ["None of the time", "A little of the time", "Some or a little of the time",
    "Occasionally or a moderate amount of the time", "Most of the time", 
    "All of the time", "Prefer not to answer"],

    ["None of the time", "A little of the time", "A moderate amount of time",
    "Most of the time", "All of the time", "Not applicable", "Prefer not to answer"],
    
    ["Strongly Agree", "Agree", "Neither Agree nor Disagree", "Disagree",
    "Strongly Disagree", "Prefer not to answer"],

    ["Yes", "No", "Not sure", "Prefer not to answer"]
]


def get_all_standard_lists(unique_answers):
    """
    Returns the complete list of answers that contains all the unique answers.
    If the unique answers are not part of any complete list, returns None.
    If the unique answers are part of multiple complete lists, returns all of them.
    """
    unique_answers = [a.lower() for a in unique_answers]
    lists = []
    for answer_list in ANSWER_LISTS:
        list_lower = [a.lower() for a in answer_list]
        if all(answer in list_lower for answer in unique_answers):
            lists.append(answer_list)
    return lists

def get_standard_list(unique_answers):
    """
    Returns the complete list of answers that contains all the unique answers.
    If the unique answers are not part of any complete list, returns None.
    If the unique answers are part of multiple complete lists, returns the first one.
    """
    lists = get_all_standard_lists(unique_answers)
    if len(lists) == 0:
        return None
    return lists[0]

def is_standard_multiple_choice(unique_answers):
    return len(get_all_standard_lists(unique_answers)) > 0

def same_standard_answer_list(answer_list1, answer_list2):
    """
    Returns True if the two lists of answes correspond to the same standard list.
    If the lists are not standard, returns False.
    If the lists are standard but different, returns False.
    If the answer lists possibly correspond to a set of multiple standard lists, it returns true
    if one set is a subset of the other.
    """
    if not is_standard_multiple_choice(answer_list1) or not is_standard_multiple_choice(answer_list2):
        return False
    std_list1 = get_all_standard_lists(answer_list1)
    std_list2 = get_all_standard_lists(answer_list2)
    # return true if one of the lists is a subset of the other
    return all(a in std_list2 for a in std_list1) or all(a in std_list1 for a in std_list2)

def get_index_in_standard_list(answer_list, answer):
    """
    Returns the index of the answer in the complete answer list.
    Useful to order the answers in a standard way.
    """
    return get_all_standard_lists(answer_list)[0].index(answer.lower())

def get_standard_list_code(unique_answers):
    """
    Returns the code of the list of answers.
    Useful to identify which questions have the same answer list.
    """
    if not is_standard_multiple_choice(unique_answers):
        return -1
    return ANSWER_LISTS.index(get_all_standard_lists(unique_answers))

def get_standard_list_from_code(code):
    """
    Returns the standard list corresponding to the code.
    """
    return ANSWER_LISTS[code]

def is_compatible_with_code(unique_answers, code):
    """
    Returns True if the unique answers are compatible with the standard list code.
    """
    for l in get_all_standard_lists(unique_answers):
        if ANSWER_LISTS[code] == l:
            return True