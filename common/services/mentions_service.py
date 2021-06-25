import re


class MentionsService(object):
    @staticmethod
    def get_mentions(text):
        # type: (unicode) -> list[unicode]
        regex = r'\[url=.*?\/users\/(.*?)\/\]@.*?\[\/url\]|\[quote="(.*?)"\].*?\[\/quote\]'
        matches = re.finditer(regex, text, re.MULTILINE)
        mentions = []

        for matchNum, match in enumerate(matches, start=1):
            for group in match.groups():
                if group is not None:
                    mentions.append(group)

        return list(set(mentions))
