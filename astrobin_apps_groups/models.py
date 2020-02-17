from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from pybb.models import Forum, Category


class Group(models.Model):
    GROUP_CATEGORY_CHOICES = (
        (1, _("Professional network")),
        (11, _("Club or association")),
        (21, _("Internet community")),
        (31, _("Friends or partners")),
        (41, _("Geographical area")),
        (51, _("Ad-hoc collaboration")),
        (61, _("Specific to an imaging technique")),
        (71, _("Specific to an astrophotography target")),
        (81, _("Specific to certain equipment")),
        (101, _("Other")),
    )

    date_created = models.DateTimeField(
        null=False,
        blank=False,
        auto_now_add=True,
        editable=False,
    )

    date_updated = models.DateTimeField(
        null=False,
        blank=False,
        auto_now=True,
        editable=False,
    )

    creator = models.ForeignKey(
        User,
        null=False,
        blank=False,
        editable=False,
        related_name='created_group_set',
    )

    owner = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name='owned_group_set',
    )

    name = models.CharField(
        max_length=512,
        null=False,
        blank=False,
        unique=True,
        verbose_name=_("Name"),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("HTML tags are allowed."),
    )

    category = models.PositiveSmallIntegerField(
        choices=GROUP_CATEGORY_CHOICES,
        null=False,
        blank=False,
        verbose_name=_("Category"),
    )

    public = models.BooleanField(
        default=False,
        verbose_name=_("Public group"),
        help_text=_("Public groups can be searched by anyone, and all their content is public."),
    )

    moderated = models.BooleanField(
        default=False,
        verbose_name=_("Moderated group"),
        help_text=_("Moderated groups have a moderation queue for posted images and join requests."),
    )

    autosubmission = models.BooleanField(
        default=False,
        verbose_name=_("Automatic submission"),
        help_text=_(
            "Groups with automatic submissions always contain all public images from all members. Groups without automatic submission only contain images that are explicitly submitted to it."),
    )

    moderators = models.ManyToManyField(
        User,
        related_name='moderated_group_set',
        blank=True,
    )

    members = models.ManyToManyField(
        User,
        related_name='joined_group_set',
        blank=True,
    )

    invited_users = models.ManyToManyField(
        User,
        related_name='invited_group_set',
        blank=True,
    )

    join_requests = models.ManyToManyField(
        User,
        related_name='join_requested_group_set',
        blank=True,
    )

    images = models.ManyToManyField(
        'astrobin.Image',
        related_name='part_of_group_set',
        blank=True,
    )

    forum = models.OneToOneField(
        Forum,
        null=True,
        blank=True,
        editable=False,
        related_name='group',
    )

    @property
    def members_count(self):
        return self.members.count()

    @property
    def images_count(self):
        return self.images.count()

    def category_humanized(self):
        for cat in self.GROUP_CATEGORY_CHOICES:
            if self.category == cat[0]:
                return cat[1]
        return ""

    def save(self, *args, **kwargs):
        if self.pk is None:
            category, created = Category.objects.get_or_create(
                name='Group forums',
                slug='group-forums',
            )

            self.forum, created = Forum.objects.get_or_create(
                category=category,
                name=self.name,
            )

        super(Group, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('group_detail', kwargs={'pk': self.pk})

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin_apps_groups'
        ordering = ['date_updated']
