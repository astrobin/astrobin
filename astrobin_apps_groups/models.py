# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Third party
from pybb.models import Forum, Category

# AstroBin
from astrobin.models import Image


class Group(models.Model):
    GROUP_CATEGORY_CHOICES = (
        (1,  _("Professional network")),
        (11, _("Club or association")),
        (21, _("Internet community")),
        (31, _("Friends or partners")),
        (41, _("Geographical area")),
        (51, _("Ad-hoc collaboration")),
        (101, _("Other")),
    )

    date_created = models.DateField(
        null = False,
        blank = False,
        auto_now_add = True,
        editable = False,
    )

    date_updated = models.DateField(
        null = False,
        blank = False,
        auto_now = True,
        editable = False,
    )

    creator = models.ForeignKey(
        User,
        null = False,
        blank = False,
        editable = False,
        related_name = 'created_group_set',
    ) 

    owner = models.ForeignKey(
        User,
        null = False,
        blank = False,
        related_name = 'owned_group_set',
    )

    name = models.CharField(
        max_length = 512,
        null = False,
        blank = False,
        unique = True,
        verbose_name = _("Name"),
    )

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
    )

    category = models.PositiveSmallIntegerField(
        choices = GROUP_CATEGORY_CHOICES,
        null = False,
        blank = False,
        verbose_name = _("Category"),
    )

    public = models.BooleanField(
        default = False,
        verbose_name = _("Public group"),
        help_text = _("Public groups can be searched by anyone, and all their content is public."),
    )

    moderated = models.BooleanField(
        default = False,
        verbose_name = _("Moderated group"),
        help_text = _("Moderated groups have a moderation queue for posted images and join requests."),
    )

    autosubmission = models.BooleanField(
        default = True,
        verbose_name = _("Automatic submission"),
        help_text = _("Groups with automatic submissions always contain all public images from all members. Groups without automatic submission only contain images that are explicitly submitted to it."),
    )

    moderators = models.ManyToManyField(
        User,
        null = True,
        blank = True,
        related_name = 'moderated_group_set',
    )

    members = models.ManyToManyField(
        User,
        null = True,
        blank = True,
        related_name = 'joined_group_set',
    )

    invited_users = models.ManyToManyField(
        User,
        null = True,
        blank = True,
        related_name = 'invited_group_set',
    )

    join_requests = models.ManyToManyField(
        User,
        null = True,
        blank = True,
        related_name = 'join_requested_group_set',
    )

    _images = models.ManyToManyField(
        Image,
        null = True,
        blank = True,
        related_name = 'part_of_group_set',
    )

    forum = models.OneToOneField(
        Forum,
        null = True,
        blank = True,
        editable = False,
        related_name = 'group',
    )

    @property
    def images(self):
        if self.autosubmission:
            return Image.objects.filter(user__in = self.members.all())
        return self._images

    @images.setter
    def images(self, value):
        self._images = value

    def save(self, *args, **kwargs):
        if self.pk is None:
            category, created = Category.objects.get_or_create(
                name = 'Group forums',
                slug = 'group-forums',
            )

            self.forum, created = Forum.objects.get_or_create(
                category = category,
                name = self.name,
            )

        super(Group, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin_apps_groups'
        ordering = ['-date_created']
