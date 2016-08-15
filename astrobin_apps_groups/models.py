# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

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
        editable = False,
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

    members = models.ManyToManyField(
        User,
        null = True,
        blank = True,
        editable = False,
        related_name = 'joined_group_set',
    )

    invited_users = models.ManyToManyField(
        User,
        null = True,
        blank = True,
        editable = False,
        related_name = 'invited_group_set',
    )

    images = models.ManyToManyField(
        Image,
        null = True,
        blank = True,
        editable = False,
        related_name = 'part_of_group_set',
    )

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin_apps_groups'
        ordering = ['-date_created']
