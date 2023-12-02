from pybb.markup.bbcode import BBCodeParser
from pybb.models import Post


class AstroBinBBCodeParser(BBCodeParser):
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
