from django.forms import Select


class SelectWithDisabledChoices(Select):
    def __init__(self, attrs=None, choices=(), disabled_choices=()):
        super(SelectWithDisabledChoices, self).__init__(attrs, choices=choices)
        self.disabled_choices = disabled_choices

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        if option.get('value') == '__DISABLED__':
            option['attrs']['disabled'] = True

        return option
