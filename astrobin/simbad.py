import urllib2
import simplejson
import re

from django.conf import settings
from django.db import IntegrityError

from models import Subject, SubjectIdentifier

def find_subjects(q):
    regex = ".*"
    for c in re.sub(r'\s', '', q):
        esc = re.escape(c)
        for d in esc:
            regex += "%c.*" % d

    url = settings.SIMBAD_SEARCH_QUERY_URL + urllib2.quote(q)
    json_string = ""
    try:
        f = urllib2.urlopen(url, timeout=1)
        json_string = f.read()
    except:
        return [] 

    f.close()

    try:
        # json will be a list of dictionaries with simbad objects.
        json = simplejson.loads(json_string)
    except simplejson.JSONDecodeError:
        # Malformatted query and Simbad didn't accept it. Let's
        # ignore it
        return []

    values = []
    for obj in json:
        found = False

        # We need to add it to our database first. We
        # are actally saving this early, because the user might
        # just disregard this result and select another, or
        # navigate away from the page. This might not be
        # optimal, but we need to have an object id in our
        # database if the user does decide to use this object.
        s = Subject()
        s.initFromJSON(obj)
        try:
            s.save()
        except IntegrityError:
            # Sometimes, for a racecondition somewhere, if the
            # user tries to lookups names really fast, a name that
            # is going to the database gets looked up again before
            # it really is there. So we try to save it again and
            # get the IntegrityError because of the duplicate key.
            s = Subject.objects.get(mainId=obj['mainId'])

        # We need to make sure that q is part of the mainId, or the
        # ui will be very confused. If that's not the case, then
        # we construct a string that has both the mainId and the id
        # that was found, just like above.
        if re.match(regex, obj['mainId'], flags=re.IGNORECASE):
            found = True
            values.append(s)

        # The id that matched q is actually one of the
        # alternative ids. Let's find it.
        for id in obj['idlist']:
            # We've got to save also all the alternative ids
            # in our database if we want to stay true to our
            # caching philosophy.
            sid = SubjectIdentifier(identifier=id, subject=s)
            try:
                sid.save()
            except IntegrityError:
                # It looks like we picked this name on a previous
                # pass. It's all right.
                pass
            if not found and re.match(regex, id, flags=re.IGNORECASE):
                values.append(s)

    return values

