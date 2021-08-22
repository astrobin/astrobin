from django import forms

from common.models.abuse_report import AbuseReport


class AbuseReportForm(forms.ModelForm):
    class Meta:
        model = AbuseReport

        fields = (
            'reason',
            'additional_information',
        )

        widgets = {
            'additional_information': forms.Textarea(attrs={'cols': '4'}),
        }
