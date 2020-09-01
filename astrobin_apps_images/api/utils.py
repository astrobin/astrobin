# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import hashlib
import os
import sys
import tempfile

import six
from django.core.cache import cache

from astrobin_apps_images.api import constants
from astrobin_apps_images.api.compat import encode_base64
from astrobin_apps_images.api.constants import TUS_RESUMABLE_FIELD_NAME


def has_required_tus_header(request):
    return request.META.get(TUS_RESUMABLE_FIELD_NAME, None) is not None


def add_expiry_header(expiration, headers):
    headers['Upload-Expires'] = expiration.strftime('%a, %d %b %Y %H:%M:%S %Z')


def encode_base64_to_string(data):
    """
    Helper to encode a string or bytes value to a base64 string as bytes
    :param six.text_types data:
    :return six.binary_type:
    """

    if not isinstance(data, six.binary_type):
        if isinstance(data, six.text_type):
            data = data.encode('utf-8')
        else:
            data = six.text_type(data).encode('utf-8')

    return encode_base64(data).decode('ascii').rstrip('\n')


def decode_upload_metadata(upload_metadata):
    metadata = {}
    for kv in upload_metadata.split(","):
        (key, value) = kv.split(" ")
        metadata[key] = base64.b64decode(value).decode("utf-8")

    return metadata


def encode_upload_metadata(upload_metadata):
    """
    Encodes upload metadata according to the TUS 1.0.0 spec (http://tus.io/protocols/resumable-upload.html#creation)
    :param dict upload_metadata:
    :return str:
    """
    # Prepare encoded data
    encoded_data = [(key, encode_base64_to_string(value))
                    for (key, value) in sorted(upload_metadata.items(), key=lambda item: item[0])]

    # Encode into string
    return ','.join([' '.join([key, encoded_value]) for key, encoded_value in encoded_data])


def write_bytes_to_file(file_path, offset, bytes, makedirs=False):
    """
    Util to write bytes to a local file at a specific offset
    :param str file_path:
    :param int offset:
    :param six.binary_type bytes:
    :param bool makedirs: Whether or not to create the file_path's directories if they don't exist
    :return int: The amount of bytes written
    """
    if makedirs:
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

    num_bytes_written = -1

    fh = None
    try:
        try:
            fh = open(file_path, 'r+b')
        except IOError:
            fh = open(file_path, 'wb')
        fh.seek(offset, os.SEEK_SET)
        num_bytes_written = fh.write(bytes)
    finally:
        if fh is not None:
            fh.close()

    # For python version < 3, "fh.write" will return None...
    if sys.version_info[0] < 3:
        num_bytes_written = len(bytes)

    return num_bytes_written


def read_bytes_from_field_file(field_file):
    """
    Returns the bytes read from a FieldFile
    :param ~django.db.models.fields.files.FieldFile field_file:
    :return six.binary_type: bytes read from the given field_file
    """
    try:
        field_file.open()
        result = field_file.read()
    finally:
        field_file.close()
    return result


def read_bytes(path):
    """
    Returns the bytes read from a local file at the given path
    :param str path: The local path to the file to read
    :return six.binary_type: bytes read from the given field_file
    """
    with open(path, 'r+b') as fh:
        result = fh.read()
    return result


def write_chunk_to_temp_file(bytes):
    """
    Write some bytes to a local temporary file and return the path
    :param six.binary_type bytes: The bytes to write
    :return str: The local path to the temporary file that has been written
    """
    fd, chunk_file = tempfile.mkstemp(prefix="tus-upload-chunk-")
    os.close(fd)

    with open(chunk_file, 'wb') as fh:
        fh.write(bytes)

    return chunk_file


def create_checksum(bytes, checksum_algorithm):
    """
    Create a hex-checksum for the given bytes using the given algorithm
    :param six.binary_type bytes: The bytes to create the checksum for
    :param str checksum_algorithm: The algorithm to use (e.g. "md5")
    :return str: The checksum (hex)
    """
    m = hashlib.new(checksum_algorithm)
    m.update(bytes)
    return m.hexdigest()


def create_checksum_header(bytes, checksum_algorithm):
    """
    Creates a hex-checksum header for the given bytes using the given algorithm
    :param six.binary_type bytes: The bytes to create the checksum for
    :param str checksum_algorithm: The algorithm to use (e.g. "md5")
    :return str: The checksum algorithm, followed by the checksum (hex)
    """
    checksum = create_checksum(bytes, checksum_algorithm)
    return '{checksum_algorithm} {checksum}'.format(checksum_algorithm=checksum_algorithm, checksum=checksum)


def checksum_matches(checksum_algorithm, checksum, bytes):
    """
    Checks if the given checksum matches the checksum for the data in the file
    :param str checksum_algorithm: The checksum algorithm to use
    :param str checksum: The original hex-checksum to match against
    :param six.binary_type bytes: The bytes to check
    :return bool: Whether or not the newly calculated checksum matches the given checksum
    """
    bytes_checksum = create_checksum(bytes, checksum_algorithm)
    return bytes_checksum == checksum


def get_or_create_temporary_file(image):
    if not get_cached_property("temporary-file-path", image):
        fd, path = tempfile.mkstemp(prefix="tus-upload-")
        os.close(fd)
        set_cached_property("temporary-file-path", image, path)

    cached = get_cached_property("temporary-file-path", image)
    assert os.path.isfile(cached)
    return cached


def write_data(image, bytes):
    temporary_file_path = get_cached_property("temporary-file-path", image)
    upload_offset = get_cached_property("offset", image)
    num_bytes_written = write_bytes_to_file(temporary_file_path, upload_offset, bytes, makedirs=True)

    if num_bytes_written > 0:
        set_cached_property("offset", image, upload_offset + num_bytes_written)


def apply_headers_to_response(response, headers):
    for item in headers.items():
        response[item[0]] = item[1]

    return response


def get_cached_property(property, object):
    return cache.get("tus-uploads/{}/{}/{}".format(object.__class__.__name__, object.pk, property))

def set_cached_property(property, object, value):
    cache.set("tus-uploads/{}/{}/{}".format(
        object.__class__.__name__, object.pk, property), value, constants.TUS_CACHE_TIMEOUT)
