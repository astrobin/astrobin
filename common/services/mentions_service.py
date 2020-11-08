import re


class MentionsService(object):
    @staticmethod
    def get_mentions(text):
        # type: (unicode) -> list[unicode]
        regex = r'\[url=.*?\/users\/(.*?)\/\]@(.*?)\[\/url\]'
        matches = re.finditer(regex, text, re.MULTILINE)
        mentions = []

        for matchNum, match in enumerate(matches, start=1):
            mention = match.groups(1)[0]
            mentions.append(mention)

        return list(set(mentions))
