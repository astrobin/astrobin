import json

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.db.models import Max
from subscription.models import Subscription, UserSubscription

from rawdata.utils import md5_for_file


# Utility functions
def max_id(Klass):
    new_id = Klass.objects.aggregate(Max('id'))['id__max']
    if new_id is None:
        new_id = 1
    return new_id


def setup_data(testcase):
    # Groups
    Group.objects.create(name="Producers")
    Group.objects.create(name="Retailers")
    Group.objects.create(name="Paying")

    Group.objects.create(name="affiliate-1")
    Group.objects.create(name="affiliate-10")
    Group.objects.create(name="affiliate-50")
    Group.objects.create(name="affiliate-100")
    Group.objects.create(name="affiliate-inf")
    Group.objects.create(name="retailer-affiliate-1")
    Group.objects.create(name="retailer-affiliate-10")
    Group.objects.create(name="retailer-affiliate-50")
    Group.objects.create(name="retailer-affiliate-100")
    Group.objects.create(name="retailer-affiliate-inf")

    Group.objects.create(name="everyone")

    rawdata_atom_group = Group.objects.create(name="rawdata-atom")
    rawdata_meteor_group = Group.objects.create(name="rawdata-meteor")
    rawdata_luna_group = Group.objects.create(name="rawdata-luna")
    rawdata_sol_group = Group.objects.create(name="rawdata-sol")
    rawdata_galaxia_group = Group.objects.create(name="rawdata-galaxia")

    rawdata_atom_2020_group = Group.objects.create(name="rawdata-atom-2020")
    rawdata_meteor_2020_group = Group.objects.create(name="rawdata-meteor-2020")
    rawdata_luna_2020_group = Group.objects.create(name="rawdata-luna-2020")
    rawdata_sol_2020_group = Group.objects.create(name="rawdata-sol-2020")
    rawdata_galaxia_2020_group = Group.objects.create(name="rawdata-galaxia-2020")

    donor_coffee_monthly_group = Group.objects.create(name="astrobin-donor-coffee-monthly")
    donor_snack_monthly_group = Group.objects.create(name="astrobin-donor-snack-monthly")
    donor_pizza_monthly_group = Group.objects.create(name="astrobin-donor-pizza-monthly")
    donor_movie_monthly_group = Group.objects.create(name="astrobin-donor-movie-monthly")
    donor_dinner_monthly_group = Group.objects.create(name="astrobin-donor-dinner-monthly")

    donor_coffee_yearly_group = Group.objects.create(name="astrobin-donor-coffee-yearly")
    donor_snack_yearly_group = Group.objects.create(name="astrobin-donor-snack-yearly")
    donor_pizza_yearly_group = Group.objects.create(name="astrobin-donor-pizza-yearly")
    donor_movie_yearly_group = Group.objects.create(name="astrobin-donor-movie-yearly")
    donor_dinner_yearly_group = Group.objects.create(name="astrobin-donor-dinner-yearly")

    donor_bronze_monthly_group = Group.objects.create(name="astrobin-donor-bronze-monthly")
    donor_silver_monthly_group = Group.objects.create(name="astrobin-donor-silver-monthly")
    donor_gold_monthly_group = Group.objects.create(name="astrobin-donor-gold-monthly")
    donor_platinum_monthly_group = Group.objects.create(name="astrobin-donor-platinum-monthly")

    donor_bronze_yearly_group = Group.objects.create(name="astrobin-donor-bronze-yearly")
    donor_silver_yearly_group = Group.objects.create(name="astrobin-donor-silver-yearly")
    donor_gold_yearly_group = Group.objects.create(name="astrobin-donor-gold-yearly")
    donor_platinum_yearly_group = Group.objects.create(name="astrobin-donor-platinum-yearly")

    # Subscriptions
    Subscription.objects.create(name="Atom", description="512 MB", price=0, recurrence_period=100, recurrence_unit="Y",
                                group=rawdata_atom_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="Meteor", description="5 GB", price=2.95, recurrence_period=1, recurrence_unit="M",
                                group=rawdata_meteor_group, trial_period=7, trial_unit="D")
    Subscription.objects.create(name="Luna", description="100 GB", price=9.95, recurrence_period=1, recurrence_unit="M",
                                group=rawdata_luna_group, trial_period=7, trial_unit="D")
    Subscription.objects.create(name="Sol", description="250 GB", price=19.95, recurrence_period=1, recurrence_unit="M",
                                group=rawdata_sol_group, trial_period=7, trial_unit="D")
    Subscription.objects.create(name="Galaxia", description="500 GB", price=49.95, recurrence_period=1,
                                recurrence_unit="M", group=rawdata_galaxia_group, trial_period=7, trial_unit="D")

    Subscription.objects.create(name="Atom 2020+", description="5 GB", price=0, recurrence_period=100,
                                recurrence_unit="Y", group=rawdata_atom_2020_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="Meteor 2020+", description="50 GB", price=3, currency="CHF", recurrence_period=1,
                                recurrence_unit="M", group=rawdata_meteor_2020_group, trial_period=7, trial_unit="D")
    Subscription.objects.create(name="Luna 2020+", description="250 GB", price=15, currency="CHF", recurrence_period=1,
                                recurrence_unit="M", group=rawdata_luna_2020_group, trial_period=7, trial_unit="D")
    Subscription.objects.create(name="Sol 2020+", description="500 GB", price=30, currency="CHF", recurrence_period=1,
                                recurrence_unit="M", group=rawdata_sol_2020_group, trial_period=7, trial_unit="D")
    Subscription.objects.create(name="Galaxia 2020+", description="1000 GB", price=60, currency="CHF",
                                recurrence_period=1, recurrence_unit="M", group=rawdata_galaxia_2020_group,
                                trial_period=7, trial_unit="D")

    Subscription.objects.create(name="AstroBin Donor Coffee Monthly", description="", price=2.50, recurrence_period=1,
                                recurrence_unit="M", group=donor_coffee_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Snack Monthly", description="", price=3.50, recurrence_period=1,
                                recurrence_unit="M", group=donor_snack_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Pizza Monthly", description="", price=6.00, recurrence_period=1,
                                recurrence_unit="M", group=donor_pizza_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Movie Monthly", description="", price=10.00, recurrence_period=1,
                                recurrence_unit="M", group=donor_movie_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Dinner Monthly", description="", price=25.00, recurrence_period=1,
                                recurrence_unit="M", group=donor_dinner_monthly_group, trial_period=0, trial_unit="D")

    Subscription.objects.create(name="AstroBin Donor Coffee Yearly", description="", price=24.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_coffee_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Snack Yearly", description="", price=34.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_snack_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Pizza Yearly", description="", price=60.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_pizza_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Movie Yearly", description="", price=100.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_movie_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Dinner Yearly", description="", price=250.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_dinner_yearly_group, trial_period=0, trial_unit="D")

    Subscription.objects.create(name="AstroBin Donor Bronze Monthly", description="", price=2.50, recurrence_period=1,
                                recurrence_unit="M", group=donor_bronze_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Silver Monthly", description="", price=5.00, recurrence_period=1,
                                recurrence_unit="M", group=donor_silver_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Gold Monthly", description="", price=10.00, recurrence_period=1,
                                recurrence_unit="M", group=donor_gold_monthly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Platinum Monthly", description="", price=20.00,
                                recurrence_period=1,
                                recurrence_unit="M", group=donor_platinum_monthly_group, trial_period=0, trial_unit="D")

    Subscription.objects.create(name="AstroBin Donor Bronze Yearly", description="", price=27.50, recurrence_period=1,
                                recurrence_unit="Y", group=donor_bronze_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Silver Yearly", description="", price=55.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_silver_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Gold Yearly", description="", price=110.00, recurrence_period=1,
                                recurrence_unit="Y", group=donor_gold_yearly_group, trial_period=0, trial_unit="D")
    Subscription.objects.create(name="AstroBin Donor Platinum Yearly", description="", price=220.00,
                                recurrence_period=1,
                                recurrence_unit="Y", group=donor_platinum_yearly_group, trial_period=0, trial_unit="D")

    testcase.unsubscribed_user = User.objects.create_user('username_unsub', 'fake0@email.tld', 'passw0rd')
    testcase.subscribed_user = User.objects.create_user('username_sub', 'fake1@email.tld', 'passw0rd')
    testcase.subscribed_user_2 = User.objects.create_user('username_sub_2', 'fake2@email.tld', 'passw0rd')
    testcase.subscribed_user_3 = User.objects.create_user('username_sub_3', 'fake3@email.tld', 'passw0rd')

    testcase.group = Group.objects.create(name='rawdata-test')
    testcase.group.user_set.add(testcase.subscribed_user, testcase.subscribed_user_2)

    testcase.group_empty = Group.objects.create(name='rawdata-empty')
    testcase.group_empty.user_set.add(testcase.subscribed_user_3)

    testcase.subscription = Subscription.objects.create(
        name='test_subscription',
        price=1.0,
        group=testcase.group)
    testcase.subscription_empty = Subscription.objects.create(
        name='test_subscription_empty',
        price=1.0,
        group=testcase.group_empty)

    testcase.user_subscription = UserSubscription.objects.create(
        user=testcase.subscribed_user,
        subscription=testcase.subscription,
        cancelled=False)

    testcase.user_subscription_2 = UserSubscription.objects.create(
        user=testcase.subscribed_user_2,
        subscription=testcase.subscription,
        cancelled=False)
    testcase.user_subscription_3 = UserSubscription.objects.create(
        user=testcase.subscribed_user_3,
        subscription=testcase.subscription_empty,
        cancelled=False)


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


def test_response(testcase, url, data, expected_status_code=200,
                  expected_field=None, expected_message=None):
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
    testcase.client.login(username='username_sub', password='passw0rd')
    response = test_response(
        testcase,
        reverse('api.rawdata.rawimage.list'),
        {'file': f, 'file_hash': h},
        201)
    testcase.client.logout()
    return response['id']


def upload_unsupported_file(testcase):
    f, h = get_unsupported_file()
    testcase.client.login(username='username_sub', password='passw0rd')
    response = test_response(
        testcase,
        reverse('api.rawdata.rawimage.list'),
        {'file': f, 'file_hash': h},
        201)
    testcase.client.logout()
    return response['id']
