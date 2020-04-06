from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from astrobin.enums import SubjectType
from astrobin.forms import ImageEditBasicForm
from astrobin.tests.generators import Generators


class ImageEditBasicFormTest(TestCase):
    def __get_valid_data(self, update={}):
        data = {
            "title": "My image",
            "acquisition_type": "TRADITIONAL",
            "data_source": "BACKYARD",
            "subject_type": SubjectType.OTHER,
        }

        data.update(update)

        return data

    def __get_files(self):
        return {
            'image_file': SimpleUploadedFile(
                'test.jpg',
                open('astrobin/fixtures/test.jpg').read(),
                'image/jpeg'
            )
        }

    def setUp(self):
        self.image = Generators.image()

    def tearDown(self):
        self.image.delete()

    def test_parse_key_value_tags_valid_data(self):
        data = self.__get_valid_data({"keyvaluetags": "foo=bar"})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertTrue(form.is_valid())

        image = form.save(commit=False)

        self.assertEquals(1, image.keyvaluetags.count())
        self.assertEquals("bar", image.keyvaluetags.get(key="foo").value)

    def test_parse_key_value_tags_valid_data_multiple_lines(self):
        data = self.__get_valid_data({"keyvaluetags": "foo=bar\r\ngoo=tar"})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertTrue(form.is_valid())

    def test_parse_key_value_tags_empty(self):
        data = self.__get_valid_data({"keyvaluetags": ""})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertTrue(form.is_valid())

    def test_parse_key_value_tags_missing_key(self):
        data = self.__get_valid_data({"keyvaluetags": "=bar"})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertFalse(form.is_valid())

    def test_parse_key_value_tags_missing_value(self):
        data = self.__get_valid_data({"keyvaluetags": "foo="})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertFalse(form.is_valid())

    def test_parse_key_value_tags_missing_key_and_value(self):
        data = self.__get_valid_data({"keyvaluetags": "="})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertFalse(form.is_valid())

    def test_parse_key_value_tags_missing_equals_sign(self):
        data = self.__get_valid_data({"keyvaluetags": "foo"})
        form = ImageEditBasicForm(instance=self.image, data=data, files=self.__get_files())

        self.assertFalse(form.is_valid())
