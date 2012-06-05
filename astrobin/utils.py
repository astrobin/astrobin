def unique_items(l):
    found = []
    for i in l:
        if i not in found:
            found.append(i)
    return found

