# Python
import json

# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.db.models import Max

# Third party apps
from subscription.models import Subscription, UserSubscription

# This app
from rawdata.utils import md5_for_file


# Utility functions
def max_id(Klass):
    new_id = Klass.objects.aggregate(Max('id'))['id__max']
    if new_id is None:
        new_id = 1
    return new_id


def setup_data(testcase):
    testcase.unsubscribed_user = User.objects.create_user('username_unsub', 'fake0@email.tld', 'passw0rd')
    testcase.subscribed_user = User.objects.create_user('username_sub', 'fake1@email.tld', 'passw0rd')
    testcase.subscribed_user_2 = User.objects.create_user('username_sub_2', 'fake2@email.tld', 'passw0rd')
    testcase.subscribed_user_3 = User.objects.create_user('username_sub_3', 'fake3@email.tld', 'passw0rd')

    testcase.group = Group.objects.create(name = 'rawdata-meteor')
    testcase.group.user_set.add(testcase.subscribed_user, testcase.subscribed_user_2)

    testcase.group_empty = Group.objects.create(name = 'rawdata-empty')
    testcase.group_empty.user_set.add(testcase.subscribed_user_3)

    testcase.subscription = Subscription.objects.create(
        name = 'test_subscription',
        price = 1.0,
        group = testcase.group)
    testcase.subscription_empty = Subscription.objects.create(
        name = 'test_subscription_empty',
        price = 1.0,
        group = testcase.group_empty)

    testcase.user_subscription = UserSubscription.objects.create(
        user = testcase.subscribed_user,
        subscription = testcase.subscription,
        cancelled = False)

    testcase.user_subscription_2 = UserSubscription.objects.create(
        user = testcase.subscribed_user_2,
        subscription = testcase.subscription,
        cancelled = False)
    testcase.user_subscription_3 = UserSubscription.objects.create(
        user = testcase.subscribed_user_3,
        subscription = testcase.subscription_empty,
        cancelled = False)


def teardown_data(testcase):
    testcase.subscribed_user.delete()
    testcase.unsubscribed_user.delete()
    testcase.group.delete()
    testcase.subscription.delete()
    testcase.user_subscription.delete()


def get_file():
    f = open('rawdata/fixtures/test.fit', 'rb')
    h = md5_for_file(f)

    f.seek(0)
    return f, h


def get_unsupported_file():
    f = open('rawdata/fixtures/test.png', 'rb')
    h = md5_for_file(f)

    f.seek(0)
    return f, h


def test_response(testcase, url, data, expected_status_code = 200,
                  expected_field = None, expected_message = None):
    response = testcase.client.post(url, data)
    response_json = json.loads(response.content)
    testcase.assertEquals(response.status_code, expected_status_code)
    if expected_field:
        testcase.assertEquals(
            response_json[expected_field][0],
            expected_message)

    return response_json

def upload_file(testcase):
    f, h = get_file()
    testcase.client.login(username = 'username_sub', password = 'passw0rd')
    response = test_response(
        testcase,
        reverse('api.rawdata.rawimage.list'),
        {'file': f, 'file_hash': h},
        201)
    testcase.client.logout()
    return response['id']

def upload_unsupported_file(testcase):
    f, h = get_unsupported_file()
    testcase.client.login(username = 'username_sub', password = 'passw0rd')
    response = test_response(
        testcase,
        reverse('api.rawdata.rawimage.list'),
        {'file': f, 'file_hash': h},
        201)
    testcase.client.logout()
    return response['id']
