from django.http import HttpResponse
import simplejson

def ajax_response(context={}):
    return HttpResponse(
        simplejson.dumps(context),
        mimetype='application/javascript')


def ajax_success(context={}):
    context['status'] = 'success'
    return ajax_response(context)


def ajax_fail(context={}):
    context['status'] = 'fail'
    return ajax_response(context)

