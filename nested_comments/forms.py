# Django
from django import forms

# This app
from .models import NestedComment


class NestedCommentForm(forms.ModelForm):
    error_css_class = 'error'

    def __init__(self, *args, **kwargs):
        super(NestedCommentForm, self).__init__(*args, **kwargs)
        self.fields['text'].label = ''

    class Meta:
        model = NestedComment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs = {
                'rows': 4,
            })
        }
