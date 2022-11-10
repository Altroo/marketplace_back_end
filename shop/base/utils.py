from re import sub, escape
from django.template.defaultfilters import slugify
from cv2 import imread, imdecode, resize, INTER_AREA, cvtColor, COLOR_BGR2RGB
from numpy import uint8, frombuffer
from PIL import Image
from io import BytesIO
from rest_framework import serializers
from django.core.files.base import ContentFile
from base64 import b64decode
from six import string_types
from uuid import uuid4
from imghdr import what
from rest_framework.views import exception_handler
from http import HTTPStatus
from typing import Any
from rest_framework.views import Response


# generate unique qaryb links
def unique_slugify(instance, value, slug_field_name, queryset=None, slug_separator='-'):
    slug_field = instance._meta.get_field(slug_field_name)
    slug_len = slug_field.max_length

    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    next_ = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '%s%s' % (slug_separator, next_)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len - len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next_ += 1

    setattr(instance, slug_field.attname, slug)
    return slug


def _slug_strip(value, separator='-'):
    separator = separator or ''
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % escape(separator)

    if separator != re_sep:
        value = sub('%s+' % re_sep, separator, value)

    if separator:
        if separator != '-':
            re_sep = escape(separator)
        value = sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)
    return value


class ImageProcessor:

    @staticmethod
    def load_image(img_path: str):
        return cvtColor(imread(img_path), COLOR_BGR2RGB)

    @staticmethod
    def load_image_from_io(bytes_: BytesIO):
        return cvtColor(imdecode(frombuffer(bytes_.read(), uint8), 1), COLOR_BGR2RGB)

    @staticmethod
    def image_resize(image, width=None, height=None, inter=INTER_AREA):
        (h, w) = image.shape[:2]

        if width is None and height is None:
            return image

        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)

        else:
            r = width / float(w)
            dim = (width, int(h * r))

        resized = resize(image, dim, interpolation=inter)
        return resized

    @staticmethod
    def from_img_to_io(image, format_):
        image = Image.fromarray(image)
        bytes_io = BytesIO()
        image.save(bytes_io, format=format_)
        bytes_io.seek(0)
        return bytes_io

    @staticmethod
    def data_url_to_uploaded_file(data):
        if isinstance(data, string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')
            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = b64decode(data)
                # Generate file name:
                file_name = str(uuid4())
                # Get the file name extension:
                file_extension = Base64ImageField.get_file_extension(file_name, decoded_file)
                complete_file_name = "%s.%s" % (file_name, file_extension,)
                data = ContentFile(decoded_file, name=complete_file_name)
                return data
            except TypeError:
                return None


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')
            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid4())
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension,)

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    @staticmethod
    def get_file_extension(file_name, decoded_file):
        extension = what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension

# def api_exception_handler_v2(exc: Exception, context: dict[str, list | Any]) -> Response:
#     """Custom API exception handler."""
#
#     # Call REST framework's default exception handler first,
#     # to get the standard error response.
#     response = exception_handler(exc, context)
#     if response is not None:
#         # Using the description's of the HTTPStatus class as error message.
#         http_code_to_message = {v.value: v.description for v in HTTPStatus}
#         error_payload = {
#             "error": {
#                 "status_code": 0,
#                 "message": "",
#                 "details": [],
#             }
#         }
#         error = error_payload["error"]
#         status_code = response.status_code
#         # if isinstance(response.data, dict):
#         if 'error' in response.data.keys():
#             if isinstance(response.data['error'], str):
#                 error["details"] = {'error' : [response.data['error']]}
#             else:
#                 error["details"] = response.data
#         elif 'detail' in response.data.keys():
#             if isinstance(response.data['detail'], str):
#                 error["details"] = {'error' : [response.data['detail']]}
#             else:
#                 error["details"] = response.data
#         else:
#             error["details"] = response.data
#         error["status_code"] = status_code
#         error["message"] = http_code_to_message[status_code]
#         # error["details"] = response.data
#         response.data = error_payload
#     return response


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """Custom API exception handler."""

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Using the description's of the HTTPStatus class as error message.
        http_code_to_message = {v.value: v.description for v in HTTPStatus}
        error_payload = {
            "error": {
                "status_code": 0,
                "message": "",
                "details": [],
            }
        }
        error = error_payload["error"]
        status_code = response.status_code

        error["status_code"] = status_code
        error["message"] = http_code_to_message[status_code]
        error["details"] = response.data
        response.data = error_payload
    return response
