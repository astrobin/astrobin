"""
    flickr.py
    Copyright 2004-2006 James Clarke <james@jamesclarke.info>
    Portions Copyright 2007-2008 Joshua Henderson <joshhendo@gmail.com>

THIS SOFTWARE IS SUPPLIED WITHOUT WARRANTY OF ANY KIND, AND MAY BE
COPIED, MODIFIED OR DISTRIBUTED IN ANY WAY, AS LONG AS THIS NOTICE
AND ACKNOWLEDGEMENT OF AUTHORSHIP REMAIN.

2007-12-17
  For an upto date TODO list, please see:
  http://code.google.com/p/flickrpy/wiki/TodoList

  For information on how to use the Authentication
  module, plese see:
  http://code.google.com/p/flickrpy/wiki/UserAuthentication

2006-12-19
  Applied patches from Berco Beute and Wolfram Kriesing.

"""

__author__ = "James Clarke <james@jamesclarke.info>"
__version__ = "$Rev$"
__date__ = "$Date$"
__copyright__ = "Copyright: 2004-2010 James Clarke; Portions: 2007-2008 Joshua Henderson"

from urllib import urlencode, urlopen
from xml.dom import minidom
import hashlib
import os

HOST = 'http://flickr.com'
API = '/services/rest'

# set these here or using flickr.API_KEY in your application
API_KEY = ''
API_SECRET = ''
email = None
password = None
AUTH = False
debug = False

# The next 2 variables are only importatnt if authentication is used

# this can be set here or using flickr.tokenPath in your application
# this is the path to the folder containing tokenFile (default: token.txt)
tokenPath = ''

# this can be set here or using flickr.tokenFile in your application
# this is the name of the file containing the stored token.
tokenFile = 'token.txt'


class FlickrError(Exception): pass

class Photo(object):
    """Represents a Flickr Photo."""

    __readonly = ['id', 'secret', 'server', 'farm', 'isfavorite', 'license', 'rotation', 
                  'owner', 'dateposted', 'datetaken', 'takengranularity', 
                  'title', 'description', 'ispublic', 'isfriend', 'isfamily', 
                  'cancomment', 'canaddmeta', 'comments', 'tags', 'permcomment', 
                  'permaddmeta']

    #XXX: Hopefully None won't cause problems
    def __init__(self, id, owner=None, dateuploaded=None, \
                 title=None, description=None, ispublic=None, \
                 isfriend=None, isfamily=None, cancomment=None, \
                 canaddmeta=None, comments=None, tags=None, secret=None, \
                 isfavorite=None, server=None, farm=None, license=None, rotation=None):
        """Must specify id, rest is optional."""
        self.__loaded = False
        self.__cancomment = cancomment
        self.__canaddmeta = canaddmeta
        self.__comments = comments
        self.__dateuploaded = dateuploaded
        self.__description = description
        self.__id = id
        self.__license = license
        self.__isfamily = isfamily
        self.__isfavorite = isfavorite
        self.__isfriend = isfriend
        self.__ispublic = ispublic
        self.__owner = owner
        self.__rotation = rotation
        self.__secret = secret
        self.__server = server
        self.__farm = farm
        self.__tags = tags
        self.__title = title
        
        self.__dateposted = None
        self.__datetaken = None
        self.__takengranularity = None
        self.__permcomment = None
        self.__permaddmeta = None
    
    def __setattr__(self, key, value):
        if key in self.__class__.__readonly:
            raise AttributeError("The attribute %s is read-only." % key)
        else:
            super(Photo, self).__setattr__(key, value)

    def __getattr__(self, key):
        if not self.__loaded:
            self._load_properties()
        if key in self.__class__.__readonly:
            return super(Photo, self).__getattribute__("_%s__%s" % (self.__class__.__name__, key))
        else:
            return super(Photo, self).__getattribute__(key)

    def _load_properties(self):
        """Loads the properties from Flickr."""
        self.__loaded = True
        
        method = 'flickr.photos.getInfo'
        data = _doget(method, photo_id=self.id)
        
        photo = data.rsp.photo

        self.__secret = photo.secret
        self.__server = photo.server
        self.__farm = photo.farm        
        self.__isfavorite = photo.isfavorite
        self.__license = photo.license
        self.__rotation = photo.rotation
        


        owner = photo.owner
        self.__owner = User(owner.nsid, username=owner.username,\
                          realname=owner.realname,\
                          location=owner.location)

        self.__title = photo.title.text
        self.__description = photo.description.text
        self.__ispublic = photo.visibility.ispublic
        self.__isfriend = photo.visibility.isfriend
        self.__isfamily = photo.visibility.isfamily

        self.__dateposted = photo.dates.posted
        self.__datetaken = photo.dates.taken
        self.__takengranularity = photo.dates.takengranularity
        
        self.__cancomment = photo.editability.cancomment
        self.__canaddmeta = photo.editability.canaddmeta
        self.__comments = photo.comments.text

        try:
            self.__permcomment = photo.permissions.permcomment
            self.__permaddmeta = photo.permissions.permaddmeta
        except AttributeError:
            self.__permcomment = None
            self.__permaddmeta = None

        #TODO: Implement Notes?
        if hasattr(photo.tags, "tag"):
            if isinstance(photo.tags.tag, list):
                self.__tags = [Tag(tag.id, User(tag.author), tag.raw, tag.text) \
                               for tag in photo.tags.tag]
            else:
                tag = photo.tags.tag
                self.__tags = [Tag(tag.id, User(tag.author), tag.raw, tag.text)]


    def __str__(self):
        return '<Flickr Photo %s>' % self.id
    

    def setTags(self, tags):
        """Set the tags for current photo to list tags.
        (flickr.photos.settags)
        """
        method = 'flickr.photos.setTags'
        tags = uniq(tags)
        _dopost(method, auth=True, photo_id=self.id, tags=tags)
        self._load_properties()


    def addTags(self, tags):
        """Adds the list of tags to current tags. (flickr.photos.addtags)
        """
        method = 'flickr.photos.addTags'
        if isinstance(tags, list):
            tags = uniq(tags)

        _dopost(method, auth=True, photo_id=self.id, tags=tags)
        #load properties again
        self._load_properties()

    def removeTag(self, tag):
        """Remove the tag from the photo must be a Tag object.
        (flickr.photos.removeTag)
        """
        method = 'flickr.photos.removeTag'
        tag_id = ''
        try:
            tag_id = tag.id
        except AttributeError:
            raise FlickrError, "Tag object expected"
        _dopost(method, auth=True, photo_id=self.id, tag_id=tag_id)
        self._load_properties()


    def setMeta(self, title=None, description=None):
        """Set metadata for photo. (flickr.photos.setMeta)"""
        method = 'flickr.photos.setMeta'

        if title is None:
            title = self.title
        if description is None:
            description = self.description
            
        _dopost(method, auth=True, title=title, \
               description=description, photo_id=self.id)
        
        self.__title = title
        self.__description = description

    
    def getURL(self, size='Medium', urlType='url'):
        """Retrieves a url for the photo.  (flickr.photos.getSizes)

        urlType - 'url' or 'source'
        'url' - flickr page of photo
        'source' - image file
        """
        method = 'flickr.photos.getSizes'
        data = _doget(method, photo_id=self.id)
        for psize in data.rsp.sizes.size:
            if psize.label == size:
                return getattr(psize, urlType)
        raise FlickrError, "No URL found"

    def getSizes(self):
        """
        Get all the available sizes of the current image, and all available
        data about them.
        Returns: A list of dicts with the size data.
        """
        method = 'flickr.photos.getSizes'
        data = _doget(method, photo_id=self.id)
        ret = []
        # The given props are those that we return and the according types, since
        # return width and height as string would make "75">"100" be True, which 
        # is just error prone.
        props = {'url':str,'width':int,'height':int,'label':str,'source':str,'text':str}
        for psize in data.rsp.sizes.size:
            d = {}
            for prop,convert_to_type in props.items():
                d[prop] = convert_to_type(getattr(psize, prop))
            ret.append(d)
        return ret
    
    #def getExif(self):
        #method = 'flickr.photos.getExif'
        #data = _doget(method, photo_id=self.id)
        #ret = []
        #for exif in data.rsp.photo.exif:
            #print exif.label, dir(exif)
            ##ret.append({exif.label:exif.})
        #return ret
        ##raise FlickrError, "No URL found"
        
    def getLocation(self):
        """
        Return the latitude+longitutde of the picture.
        Returns None if no location given for this pic.
        """
        method = 'flickr.photos.geo.getLocation'
        try:
            data = _doget(method, photo_id=self.id)
        except FlickrError: # Some other error might have occured too!?
            return None
        loc = data.rsp.photo.location
        return [loc.latitude, loc.longitude]
        
        
    def getComments(self):
        """"
        get list of comments for photo
        returns a list of comment objects
        comment text is in return [item].text
        """
        method = "flickr.photos.comments.getList"
        try:
            data = _doget(method,  photo_id=self.id)
        except FlickrError: # ???? what errors might there be????
            return None
        return data.rsp.comments
            
    def _getDirectURL(self, size):
        return "http://farm%s.static.flickr.com/%s/%s_%s_%s.jpg" % \
            (self.farm, self.server, self.id, self.secret, size)
        
    def getThumbnail(self): 
        """
        Return a string representation of the URL to the thumbnail
        image (not the thumbnail image page).
        """
        return self._getDirectURL('t')

    def getSmallSquare(self):
        """
        Return a string representation of the URL to the small square
        image (not the small square image page).
        """
        return self._getDirectURL('s')

    def getSmall(self):
        """
        Return a string representation of the URL to the small 
        image (not the small image page).
        """
        return self._getDirectURL('m')

    def getMedium(self):
        """
        Return a string representation of the URL to the medium 
        image (not the medium image page).
        """
        return self._getDirectURL('z')

    def getLarge(self):
        """
        Return a string representation of the URL to the large 
        image (not the large image page).
        """
        return self._getDirectURL('b')

                
class Photoset(object):
    """A Flickr photoset."""

    def __init__(self, id, title, primary, photos=0, description='', \
                 secret='', server=''):
        self.__id = id
        self.__title = title
        self.__primary = primary
        self.__description = description
        self.__count = photos
        self.__secret = secret
        self.__server = server
        
    id = property(lambda self: self.__id)
    title = property(lambda self: self.__title)
    description = property(lambda self: self.__description)
    primary = property(lambda self: self.__primary)

    def __len__(self):
        return self.__count

    def __str__(self):
        return '<Flickr Photoset %s>' % self.id
    
    def getPhotos(self):
        """Returns list of Photos."""
        method = 'flickr.photosets.getPhotos'
        data = _doget(method, photoset_id=self.id)
        photos = data.rsp.photoset.photo
        p = []
        for photo in photos:
            p.append(Photo(photo.id, title=photo.title, secret=photo.secret, \
                           server=photo.server))
        return p    

    def editPhotos(self, photos, primary=None):
        """Edit the photos in this set.

        photos - photos for set
        primary - primary photo (if None will used current)
        """
        method = 'flickr.photosets.editPhotos'

        if primary is None:
            primary = self.primary
            
        ids = [photo.id for photo in photos]
        if primary.id not in ids:
            ids.append(primary.id)

        _dopost(method, auth=True, photoset_id=self.id,\
                primary_photo_id=primary.id,
                photo_ids=ids)
        self.__count = len(ids)
        return True

    def addPhoto(self, photo):
        """Add a photo to this set.

        photo - the photo
        """
        method = 'flickr.photosets.addPhoto'

        _dopost(method, auth=True, photoset_id=self.id, photo_id=photo.id)

        self.__count += 1
        return True

    def removePhoto(self, photo):
        """Remove the photo from this set.

        photo - the photo
        """
        method = 'flickr.photosets.removePhoto'

        _dopost(method, auth=True, photoset_id=self.id, photo_id=photo.id)
        self.__count = self.__count - 1
        return True
        
    def editMeta(self, title=None, description=None):
        """Set metadata for photo. (flickr.photos.setMeta)"""
        method = 'flickr.photosets.editMeta'

        if title is None:
            title = self.title
        if description is None:
            description = self.description
            
        _dopost(method, auth=True, title=title, \
               description=description, photoset_id=self.id)
        
        self.__title = title
        self.__description = description
        return True

    #XXX: Delete isn't handled well as the python object will still exist
    def delete(self):
        """Deletes the photoset.
        """
        method = 'flickr.photosets.delete'

        _dopost(method, auth=True, photoset_id=self.id)
        return True

    def create(cls, photo, title, description=''):
        """Create a new photoset.

        photo - primary photo
        """
        if not isinstance(photo, Photo):
            raise TypeError, "Photo expected"
        
        method = 'flickr.photosets.create'
        data = _dopost(method, auth=True, title=title,\
                       description=description,\
                       primary_photo_id=photo.id)
        
        set = Photoset(data.rsp.photoset.id, title, Photo(photo.id),
                       photos=1, description=description)
        return set
    create = classmethod(create)
                      
        
class User(object):
    """A Flickr user."""

    def __init__(self, id, username=None, isadmin=None, ispro=None, \
                 realname=None, location=None, firstdate=None, count=None):
        """id required, rest optional."""
        self.__loaded = False #so we don't keep loading data
        self.__id = id
        self.__username = username
        self.__isadmin = isadmin
        self.__ispro = ispro
        self.__realname = realname
        self.__location = location
        self.__photos_firstdate = firstdate
        self.__photos_count = count

    #property fu
    id = property(lambda self: self._general_getattr('id'))
    username = property(lambda self: self._general_getattr('username'))
    isadmin = property(lambda self: self._general_getattr('isadmin'))
    ispro = property(lambda self: self._general_getattr('ispro'))
    realname = property(lambda self: self._general_getattr('realname'))
    location = property(lambda self: self._general_getattr('location'))
    photos_firstdate = property(lambda self: \
                                self._general_getattr('photos_firstdate'))
    photos_firstdatetaken = property(lambda self: \
                                     self._general_getattr\
                                     ('photos_firstdatetaken'))
    photos_count = property(lambda self: \
                            self._general_getattr('photos_count'))
    icon_server= property(lambda self: self._general_getattr('icon_server'))
    icon_url= property(lambda self: self._general_getattr('icon_url'))
 
    def _general_getattr(self, var):
        """Generic get attribute function."""
        if getattr(self, "_%s__%s" % (self.__class__.__name__, var)) is None \
           and not self.__loaded:
            self._load_properties()
        return getattr(self, "_%s__%s" % (self.__class__.__name__, var))
            
    def _load_properties(self):
        """Load User properties from Flickr."""
        method = 'flickr.people.getInfo'
        data = _doget(method, user_id=self.__id)

        self.__loaded = True
        
        person = data.rsp.person

        self.__isadmin = person.isadmin
        self.__ispro = person.ispro
        self.__icon_server = person.iconserver
        if int(person.iconserver) > 0:
            self.__icon_url = 'http://photos%s.flickr.com/buddyicons/%s.jpg' \
                              % (person.iconserver, self.__id)
        else:
            self.__icon_url = 'http://www.flickr.com/images/buddyicon.jpg'
        
        self.__username = person.username.text
        self.__realname = getattr((getattr(person,  'realname',  u'')), 'text', u'')
        self.__location = getattr((getattr(person,  'location',  u'')), 'text', u'')
        self.__photos_count = getattr((getattr(getattr(person,  'photos',  None),  'count',  u'')), 'text', u'')
        if self.__photos_count:
            self.__photos_firstdate = person.photos.firstdate.text
            self.__photos_firstdatetaken = person.photos.firstdatetaken.text
        else:
            self.__photos_firstdate = None
            self.__photos_firstdatetaken = None

    def __str__(self):
        return '<Flickr User %s>' % self.id
    
    def getPhotosets(self):
        """Returns a list of Photosets."""
        method = 'flickr.photosets.getList'
        data = _doget(method, user_id=self.id)
        
        sets = []
        if not getattr(data.rsp.photosets,  'photoset',None):
            return sets        #N.B. returns an empty set
        if isinstance(data.rsp.photosets.photoset, list):
            for photoset in data.rsp.photosets.photoset:
                sets.append(Photoset(photoset.id, photoset.title.text,\
                                     Photo(photoset.primary),\
                                     secret=photoset.secret, \
                                     server=photoset.server, \
                                     description=photoset.description.text,
                                     photos=photoset.photos))
        else:
            photoset = data.rsp.photosets.photoset
            sets.append(Photoset(photoset.id, photoset.title.text,\
                                     Photo(photoset.primary),\
                                     secret=photoset.secret, \
                                     server=photoset.server, \
                                     description=photoset.description.text,
                                     photos=photoset.photos))
        return sets

    def getPublicFavorites(self, per_page='', page=''):
        return favorites_getPublicList(user_id=self.id, per_page=per_page, \
                                       page=page)

    def getFavorites(self, per_page='', page=''):
        return favorites_getList(user_id=self.id, per_page=per_page, \
                                 page=page)

class Group(object):
    """Flickr Group Pool"""
    def __init__(self, id, name=None, members=None, online=None,\
                 privacy=None, chatid=None, chatcount=None):
        self.__loaded = False
        self.__id = id
        self.__name = name

        self.__members = members
        self.__online = online
        self.__privacy = privacy
        self.__chatid = chatid
        self.__chatcount = chatcount
        self.__url = None

    id = property(lambda self: self._general_getattr('id'))
    name = property(lambda self: self._general_getattr('name'))
    members = property(lambda self: self._general_getattr('members'))
    online = property(lambda self: self._general_getattr('online'))
    privacy = property(lambda self: self._general_getattr('privacy'))
    chatid = property(lambda self: self._general_getattr('chatid'))
    chatcount = property(lambda self: self._general_getattr('chatcount'))

    def _general_getattr(self, var):
        """Generic get attribute function."""
        if getattr(self, "_%s__%s" % (self.__class__.__name__, var)) is None \
           and not self.__loaded:
            self._load_properties()
        return getattr(self, "_%s__%s" % (self.__class__.__name__, var))

    def _load_properties(self):
        """Loads the properties from Flickr."""
        method = 'flickr.groups.getInfo'
        data = _doget(method, group_id=self.id)

        self.__loaded = True
        
        group = data.rsp.group

        self.__name = photo.name.text
        self.__members = photo.members.text
        self.__online = photo.online.text
        self.__privacy = photo.privacy.text
        self.__chatid = photo.chatid.text
        self.__chatcount = photo.chatcount.text

    def __str__(self):
        return '<Flickr Group %s>' % self.id
    
    def getPhotos(self, tags='', per_page='', page=''):
        """Get a list of photo objects for this group"""
        method = 'flickr.groups.pools.getPhotos'
        data = _doget(method, group_id=self.id, tags=tags,\
                      per_page=per_page, page=page)
        photos = []
        for photo in data.rsp.photos.photo:
            photos.append(_parse_photo(photo))
        return photos

    def add(self, photo):
        """Adds a Photo to the group"""
        method = 'flickr.groups.pools.add'
        _dopost(method, auth=True, photo_id=photo.id, group_id=self.id)
        return True

    def remove(self, photo):
        """Remove a Photo from the group"""
        method = 'flickr.groups.pools.remove'
        _dopost(method, auth=True, photo_id=photo.id, group_id=self.id)
        return True
    
class Tag(object):
    def __init__(self, id, author, raw, text):
        self.id = id
        self.author = author
        self.raw = raw
        self.text = text

    def __str__(self):
        return '<Flickr Tag %s (%s)>' % (self.id, self.text)

    
#Flickr API methods
#see api docs http://www.flickr.com/services/api/
#for details of each param

#XXX: Could be Photo.search(cls)
def photos_search(user_id='', auth=False,  tags='', tag_mode='', text='',\
                  min_upload_date='', max_upload_date='',\
                  min_taken_date='', max_taken_date='', \
                  license='', per_page='', page='', sort='',\
                  safe_search='', content_type='' ):
    """Returns a list of Photo objects.

    If auth=True then will auth the user.  Can see private etc
    """
    method = 'flickr.photos.search'

    data = _doget(method, auth=auth, user_id=user_id, tags=tags, text=text,\
                  min_upload_date=min_upload_date,\
                  max_upload_date=max_upload_date, \
                  min_taken_date=min_taken_date, \
                  max_taken_date=max_taken_date, \
                  license=license, per_page=per_page,\
                  page=page, sort=sort,  safe_search=safe_search, \
                  content_type=content_type, \
                  tag_mode=tag_mode)
    photos = []
    if data.rsp.photos.__dict__.has_key('photo'):
        if isinstance(data.rsp.photos.photo, list):
            for photo in data.rsp.photos.photo:
                photos.append(_parse_photo(photo))
        else:
            photos = [_parse_photo(data.rsp.photos.photo)]
    return photos

def photos_search_pages(user_id='', auth=False,  tags='', tag_mode='', text='',\
                  min_upload_date='', max_upload_date='',\
                  min_taken_date='', max_taken_date='', \
                  license='', per_page='', page='', sort=''):
    """Returns the number of pages for the previous function (photos_search())
    """
	
    method = 'flickr.photos.search'

    data = _doget(method, auth=auth, user_id=user_id, tags=tags, text=text,\
                  min_upload_date=min_upload_date,\
                  max_upload_date=max_upload_date, \
                  min_taken_date=min_taken_date, \
                  max_taken_date=max_taken_date, \
                  license=license, per_page=per_page,\
                  page=page, sort=sort)
	
    return data.rsp.photos.pages

def photos_get_recent(extras='', per_page='', page=''):
    """http://www.flickr.com/services/api/flickr.photos.getRecent.html
    """
    method = 'flickr.photos.getRecent'
    data = _doget(method, extras=extras, per_page=per_page, page=page)
    photos = []
    if data.rsp.photos.__dict__.has_key('photo'):
        if isinstance(data.rsp.photos.photo, list):
            for photo in data.rsp.photos.photo:
                photos.append(_parse_photo(photo))
        else:
            photos = [_parse_photo(data.rsp.photos.photo)]
    return photos    
	
	
#XXX: Could be class method in User
def people_findByEmail(email):
    """Returns User object."""
    method = 'flickr.people.findByEmail'
    data = _doget(method, find_email=email)
    user = User(data.rsp.user.id, username=data.rsp.user.username.text)
    return user

def people_findByUsername(username):
    """Returns User object."""
    method = 'flickr.people.findByUsername'
    data = _doget(method, username=username)
    user = User(data.rsp.user.id, username=data.rsp.user.username.text)
    return user

#XXX: Should probably be in User as a list User.public
def people_getPublicPhotos(user_id, per_page='', page=''):
    """Returns list of Photo objects."""
    method = 'flickr.people.getPublicPhotos'
    data = _doget(method, user_id=user_id, per_page=per_page, page=page)
    photos = []
    if hasattr(data.rsp.photos, "photo"): # Check if there are photos at all (may be been paging too far).
        if isinstance(data.rsp.photos.photo, list):
            for photo in data.rsp.photos.photo:
                photos.append(_parse_photo(photo))
        else:
            photos = [_parse_photo(data.rsp.photos.photo)]
    return photos

#XXX: These are also called from User
def favorites_getList(user_id='', per_page='', page=''):
    """Returns list of Photo objects."""
    method = 'flickr.favorites.getList'
    data = _doget(method, auth=True, user_id=user_id, per_page=per_page,\
                  page=page)
    photos = []
    if isinstance(data.rsp.photos.photo, list):
        for photo in data.rsp.photos.photo:
            photos.append(_parse_photo(photo))
    else:
        photos = [_parse_photo(data.rsp.photos.photo)]
    return photos

def favorites_getPublicList(user_id, per_page='', page=''):
    """Returns list of Photo objects."""
    method = 'flickr.favorites.getPublicList'
    data = _doget(method, auth=False, user_id=user_id, per_page=per_page,\
                  page=page)
    photos = []
    if isinstance(data.rsp.photos.photo, list):
        for photo in data.rsp.photos.photo:
            photos.append(_parse_photo(photo))
    else:
        photos = [_parse_photo(data.rsp.photos.photo)]
    return photos

def favorites_add(photo_id):
    """Add a photo to the user's favorites."""
    method = 'flickr.favorites.add'
    _dopost(method, auth=True, photo_id=photo_id)
    return True

def favorites_remove(photo_id):
    """Remove a photo from the user's favorites."""
    method = 'flickr.favorites.remove'
    _dopost(method, auth=True, photo_id=photo_id)
    return True

def groups_getPublicGroups():
    """Get a list of groups the auth'd user is a member of."""
    method = 'flickr.groups.getPublicGroups'
    data = _doget(method, auth=True)
    groups = []
    if isinstance(data.rsp.groups.group, list):
        for group in data.rsp.groups.group:
            groups.append(Group(group.id, name=group.name))
    else:
        group = data.rsp.groups.group
        groups = [Group(group.id, name=group.name)]
    return groups

def groups_pools_getGroups():
    """Get a list of groups the auth'd user can post photos to."""
    method = 'flickr.groups.pools.getGroups'
    data = _doget(method, auth=True)
    groups = []
    if isinstance(data.rsp.groups.group, list):
        for group in data.rsp.groups.group:
            groups.append(Group(group.id, name=group.name, \
                                privacy=group.privacy))
    else:
        group = data.rsp.groups.group
        groups = [Group(group.id, name=group.name, privacy=group.privacy)]
    return groups
    

def tags_getListUser(user_id=''):
    """Returns a list of tags for the given user (in string format)"""
    method = 'flickr.tags.getListUser'
    auth = user_id == ''
    data = _doget(method, auth=auth, user_id=user_id)
    if isinstance(data.rsp.tags.tag, list):
        return [tag.text for tag in data.rsp.tags.tag]
    else:
        return [data.rsp.tags.tag.text]

def tags_getListUserPopular(user_id='', count=''):
    """Gets the popular tags for a user in dictionary form tag=>count"""
    method = 'flickr.tags.getListUserPopular'
    auth = user_id == ''
    data = _doget(method, auth=auth, user_id=user_id)
    result = {}
    if isinstance(data.rsp.tags.tag, list):
        for tag in data.rsp.tags.tag:
            result[tag.text] = tag.count
    else:
        result[data.rsp.tags.tag.text] = data.rsp.tags.tag.count
    return result

def tags_getrelated(tag):
    """Gets the related tags for given tag."""
    method = 'flickr.tags.getRelated'
    data = _doget(method, auth=False, tag=tag)
    if isinstance(data.rsp.tags.tag, list):
        return [tag.text for tag in data.rsp.tags.tag]
    else:
        return [data.rsp.tags.tag.text]

def contacts_getPublicList(user_id):
    """Gets the contacts (Users) for the user_id"""
    method = 'flickr.contacts.getPublicList'
    data = _doget(method, auth=False, user_id=user_id)

    try:
      if isinstance(data.rsp.contacts.contact, list):
          return [User(user.nsid, username=user.username) \
                  for user in data.rsp.contacts.contact]

    except AttributeError:
      return "No users in the list"
    except:
      return "Unknown error"

#   else:
#       user = data.rsp.contacts.contact
#       return [User(user.nsid, username=user.username)]

def interestingness():
    method = 'flickr.interestingness.getList'
    data = _doget(method)
    photos = []
    if isinstance(data.rsp.photos.photo , list):
        for photo in data.rsp.photos.photo:
            photos.append(_parse_photo(photo))
    else:
        photos = [_parse_photo(data.rsp.photos.photo)]
    return photos    
    
def test_login():
    method = 'flickr.test.login'
    data = _doget(method, auth=True)
    user = User(data.rsp.user.id, username=data.rsp.user.username.text)
    return user

def test_echo():
    method = 'flickr.test.echo'
    data = _doget(method)
    return data.rsp.stat


#useful methods

def _doget(method, auth=False, **params):
    #uncomment to check you aren't killing the flickr server
    #print "***** do get %s" % method

    params = _prepare_params(params)
    url = '%s%s/?api_key=%s&method=%s&%s%s'% \
          (HOST, API, API_KEY, method, urlencode(params),
                  _get_auth_url_suffix(method, auth, params))

    #another useful debug print statement
    if debug:       
        print "_doget", url
    
    return _get_data(minidom.parse(urlopen(url)))

def _dopost(method, auth=False, **params):
    #uncomment to check you aren't killing the flickr server
    #print "***** do post %s" % method

    params = _prepare_params(params)
    url = '%s%s/?api_key=%s&method=%s&%s'% \
          (HOST, API, API_KEY, method, _get_auth_url_suffix(method, auth, params))

    # There's no reason this can't be str(urlencode(params)). I just wanted to
    # have it the same as the rest.
    payload = '%s' % (urlencode(params))

    #another useful debug print statement
    if debug:
        print "_dopost url", url
        print "_dopost payload", payload
    
    return _get_data(minidom.parse(urlopen(url, payload)))

def _prepare_params(params):
    """Convert lists to strings with ',' between items."""
    for (key, value) in params.items():
        if isinstance(value, list):
            params[key] = ','.join([item for item in value])
    return params

def _get_data(xml):
    """Given a bunch of XML back from Flickr, we turn it into a data structure
    we can deal with (after checking for errors)."""
    data = unmarshal(xml)
    if not data.rsp.stat == 'ok':
        msg = "ERROR [%s]: %s" % (data.rsp.err.code, data.rsp.err.msg)
        raise FlickrError, msg
    return data

def _get_api_sig(params):
    """Generate API signature."""
    token = userToken()
    parameters = ['api_key', 'auth_token']
    for item in params.items():
        parameters.append(item[0])
    parameters.sort()

    api_string = [API_SECRET]

    for item in parameters:
        for chocolate in params.items():
            if item == chocolate[0]:
                api_string.append(item)
                api_string.append(str(chocolate[1]))
        if item == 'api_key':
        	api_string.append('api_key')
        	api_string.append(API_KEY)
        if item == 'auth_token':
            api_string.append('auth_token')
            api_string.append(token)

    api_signature = hashlib.md5(''.join(api_string)).hexdigest()

    return api_signature

def _get_auth_url_suffix(method, auth, params):
    """Figure out whether we want to authorize, and if so, construct a suitable
    URL suffix to pass to the Flickr API."""
    authentication = False

    # auth may be passed in via the API, AUTH may be set globally (in the same
    # manner as API_KEY, etc). We do a few more checks than may seem necessary
    # because we allow the 'auth' parameter to actually contain the
    # authentication token, not just True/False.
    if auth or AUTH:
        token = userToken()
        authentication = True;
    elif auth != False:
        token = auth;
        authentication = True;
    elif AUTH != False:
        token = AUTH;
        authentication = True;

    # If we're not authenticating, no suffix is required.
    if not authentication:
        return ''

    full_params = params
    full_params['method'] = method

    return '&auth_token=%s&api_sig=%s' % (token, _get_api_sig(full_params) )

def _parse_photo(photo):
    """Create a Photo object from photo data."""
    owner = User(photo.owner)
    title = photo.title
    ispublic = photo.ispublic
    isfriend = photo.isfriend
    isfamily = photo.isfamily
    secret = photo.secret
    server = photo.server
    p = Photo(photo.id, owner=owner, title=title, ispublic=ispublic,\
              isfriend=isfriend, isfamily=isfamily, secret=secret, \
              server=server)        
    return p

#stolen methods

class Bag: pass

#unmarshal taken and modified from pyamazon.py
#makes the xml easy to work with
def unmarshal(element):
    rc = Bag()
    if isinstance(element, minidom.Element):
        for key in element.attributes.keys():
            setattr(rc, key, element.attributes[key].value)
            
    childElements = [e for e in element.childNodes \
                     if isinstance(e, minidom.Element)]
    if childElements:
        for child in childElements:
            key = child.tagName
            if hasattr(rc, key):
                if type(getattr(rc, key)) <> type([]):
                    setattr(rc, key, [getattr(rc, key)])
                setattr(rc, key, getattr(rc, key) + [unmarshal(child)])
            elif isinstance(child, minidom.Element) and \
                     (child.tagName == 'Details'):
                # make the first Details element a key
                setattr(rc,key,[unmarshal(child)])
                #dbg: because otherwise 'hasattr' only tests
                #dbg: on the second occurence: if there's a
                #dbg: single return to a query, it's not a
                #dbg: list. This module should always
                #dbg: return a list of Details objects.
            else:
                setattr(rc, key, unmarshal(child))
    else:
        #jec: we'll have the main part of the element stored in .text
        #jec: will break if tag <text> is also present
        text = "".join([e.data for e in element.childNodes \
                        if isinstance(e, minidom.Text)])
        setattr(rc, 'text', text)
    return rc

#unique items from a list from the cookbook
def uniq(alist):    # Fastest without order preserving
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()

## Only the "getList" module is complete.
## Work in Progress; Nearly Finished
class Blogs():
    def getList(self,auth=True):
        """blogs.getList requires READ authentication"""
        # please read documentation on how to use this
        
        method = 'flickr.blogs.getList'
        if auth==True : data = _doget(method, auth=True)
        if not auth==True : data = _doget(method, auth=False)
        
        bID = []
        bName = []
        bNeedsPword = []
        bURL = []
        
        try:
            for plog in data.rsp.blogs.blog:
                bID.append(plog.id)
                bName.append(plog.name)
                bNeedsPword.append(plog.needspassword)
                bURL.append(plog.url)
        except TypeError:
            try:
                bID.append(data.rsp.blogs.blog.id)
                bName.append(data.rsp.blogs.blog.name)
                bNeedsPword.append(data.rsp.blogs.blog.needspassword)
                bURL.append(data.rsp.blogs.blog.url)
            except AttributeError:
                return "AttributeError, unexplained!"
            except:
                return "Unknown error!"
        except AttributeError:
            return "There are no blogs!"
		
        myReturn = [bID,bName,bNeedsPword,bURL]
        return myReturn

    def postPhoto(self, blogID, photoID, title, description, bpassword):
        """blogs.postPhoto requires WRITE authentication"""
        method = 'flickr.blogs.postPhoto'
        return None

class Urls():
    def getUserPhotosURL(userid):
        """Returns user URL in an array (to access, use array[1])"""
        method = 'flickr.urls.getUserPhotos'
        data = _doget(method, user_id=userid)
        return [data.rsp.user.nsid,data.rsp.user.url]

class Auth():
    def getFrob(self):
        """Returns a frob that is used in authentication"""
        method = 'flickr.auth.getFrob'
        sig_str = API_SECRET + 'api_key' + API_KEY + 'method' + method
        signature_hash = hashlib.md5(sig_str).hexdigest()
        data = _doget(method, auth=False, api_sig=signature_hash)
        return data.rsp.frob.text

    def loginLink(self, permission, frob):
        """Generates a link that the user should be sent to"""
        myAuth = Auth()
        sig_str = API_SECRET + 'api_key' + API_KEY + 'frob' + frob + 'perms' + permission
        signature_hash = hashlib.md5(sig_str).hexdigest()
        perms = permission
        link = "http://flickr.com/services/auth/?api_key=%s&perms=%s&frob=%s&api_sig=%s" % (API_KEY, perms, frob, signature_hash)
        return link

    def getToken(self, frob):
        """This token is what needs to be used in future API calls"""
        method = 'flickr.auth.getToken'
        sig_str = API_SECRET + 'api_key' + API_KEY + 'frob' + frob + 'method' + method
        signature_hash = hashlib.md5(sig_str).hexdigest()
        data = _doget(method, auth=False, api_sig=signature_hash, 
                      api_key=API_KEY, frob=frob)
        return data.rsp.auth.token.text

def userToken():
    # This method allows you flickr.py to retrive the saved token
    # as once the token for a program has been got from flickr, 
    # it cannot be got again, so flickr.py saves it in a file
    # called token.txt (default) somewhere.
    if not tokenPath == '':
        f = file(os.path.join(tokenPath,tokenFile),'r')
    else:
        f = file(tokenFile,'r')
    token = f.read()
    f.close()
    return token

def getUserPhotosURL(userid):
    """Returns user URL in an array (to access, use array[1])"""
    # This addition has been added upon request of
    # nsteinmetz. It will be "cleaned up" at another
    # time.
    method = 'flickr.urls.getUserPhotos'
    data = _doget(method, user_id=userid)
    userurl = [data.rsp.user.nsid,data.rsp.user.url]
    return userurl

if __name__ == '__main__':
    print test_echo()
