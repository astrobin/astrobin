from django.core.management.commands import makemessages


class Command(makemessages.Command):
    msgmerge_options = ['-q', '--previous', '--no-fuzzy-matching']
