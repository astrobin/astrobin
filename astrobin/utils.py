def unique_items(l):
    found = []
    for i in l:
        if i not in found:
            found.append(i)
    return found


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def base26_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base26_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


def user_is_producer(user):
    is_producer = False
    if user:
        is_producer = user.groups.filter(name = 'Producers').count() > 0
    return is_producer


def user_is_retailer(user):
    if user:
        return user.groups.filter(name = 'Retailers').count() > 0
    return False 

def affiliate_limit(user):
    if not user:
        return 0

    if user.groups.filter(name = 'affiliate-'):
        return 1
    if user.groups.filter(name = 'affiliate-10'):
        return 10
    if user.groups.filter(name = 'affiliate-50'):
        return 50
    if user.groups.filter(name = 'affiliate-100'):
        return 100
    if user.groups.filter(name = 'affiliate-100'):
        return sys.maxint

    return 0

