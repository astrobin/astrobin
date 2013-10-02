# Django
from django.template import Library, Node
from django.template.loader import render_to_string

# actstream
from actstream.templatetags.activity_tags import DisplayAction


register = Library()

class AstroBinDisplayAction(DisplayAction):
    def render_result(self, context):
        wrapper = self.args[0].resolve(context)
        action_instance = wrapper['action']
        show_thumbnail = wrapper['show_thumbnail']

        templates = [
            'actstream/%s/action.html' % action_instance.verb.replace(' ', '_'),
            'actstream/action.html',
            'activity/%s/action.html' % action_instance.verb.replace(' ', '_'),
            'activity/action.html',
        ]
        return render_to_string(
            templates,
            {'action': action_instance,
             'show_thumbnail': show_thumbnail,
            },
            context)


def astrobin_display_action(parser, token):
    return AstroBinDisplayAction.handle_token(parser, token)


register.tag(astrobin_display_action)

