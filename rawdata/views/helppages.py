# Django
from django.views.generic import TemplateView
from django.contrib.staticfiles.templatetags.staticfiles import static


class Help(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(Help, self).get_context_data(**kwargs)

        prefix = 'rawdata/images/tour/%s' % (self.request.LANGUAGE_CODE\
            if 'LANGUAGE_CODE' in self.request\
            else 'en')
        context['screenshot_urls'] = [{
            'thumb': static('%s/thumbs/rawdata-tour-%02d.png' % (prefix, i)),
            'href': static('%s/rawdata-tour-%02d.png' % (prefix, i))
        } for i in range(1, 16)]

        return context

class Help1(Help):
    template_name = 'rawdata/help_01.html'

class Help2(Help):
    template_name = 'rawdata/help_02.html'

class Help3(Help):
    template_name = 'rawdata/help_03.html'
