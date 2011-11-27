from django.http import HttpResponse
import simplejson

def ajax_response(context={}):
    return HttpResponse(
        simplejson.dumps(context),
        mimetype='application/javascript')


def ajax_success(context={}):
    context['success'] = True
    return ajax_response(context)


def ajax_fail(context={}):
    context['success'] = False
    return ajax_response(context)

