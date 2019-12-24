NULL_CHOICE = [('', '---------')]


def parseKeyValueTags(tags):
    """
    Reads tags from plain texts and returns parsed list of pairs
    :type tags: basestring
    """

    list = []

    if tags:
        lines = tags.replace('\r\n', '\n').split('\n')

        for line in lines:
            if line:
                key, value = line.split('=')

                if not key or not value:
                    raise ValueError

                if len([item for item in list if item.get('key') == key]) > 0:
                    raise ValueError

                list.append({"key": key, "value": value})

    return list
