def is_premium(user):
    if not user:
        return False

    if user.groups.filter(name = 'rawdata-100'):
        return True

    return False


def byte_limit(user):
    if not user:
        return 0

    if user.groups.filter(name = 'rawdata-100'):
        return 100 * 1024*1024*1024
