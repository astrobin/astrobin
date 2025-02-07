from pybb.markup.bbcode import BBCodeParser
from pybb.models import Post


class AstroBinBBCodeParser(BBCodeParser):
    def __init__(self):
        super().__init__()
        self._parser.add_formatter('size', self.size, strip=True, swallow_trailing_newline=True)

    def quote(self, text: str, name: str = '') -> str:
        try:
            post = Post.objects.get(body=text, user__userprofile__real_name=name)
            display_name = post.user.userprofile.get_display_name()
            username = post.user.username

            if display_name == username:
                return '[quote="%s"]%s[/quote]\n' % (username, text)
            return '[quote="%s (%s)"]%s[/quote]\n' % (display_name, username, text)
        except (Post.DoesNotExist, Post.MultipleObjectsReturned):
            return '[quote="%s"]%s[/quote]\n' % (name, text)

    def size(self, tag: str, text: str, options, parent, context) -> str:
        if 'size' not in options:
            return text

        size = str(options['size']).replace('"', '')

        # Check if the size is a valid number
        if not size.isdigit():
            return text

        # Define three tiers for small, medium, and large, where <= 50% is small, <= 100% is medium, and > 100% is large
        size = int(size)
        if size <= 50:
            size = '.5rem'
        elif size <= 75:
            size = '.75rem'
        elif size <= 100:
            size = '1rem'
        elif size <= 150:
            size = '1.5rem'
        else:
            size = '2rem'

        return f'<span style="font-size: {size}">{text}</span>'
