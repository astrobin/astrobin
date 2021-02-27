from django.utils.translation import ugettext_lazy as _

TOGGLEPROPERTIES = {
    "bookmark": {
        "property_tooltip_on": _("Remove from bookmarks"),
        "property_tooltip_off": _("Bookmark"),
        "property_icon": "icon-bookmark",
    },

    "like": {
        "property_label_on": _("Unlike"),
        "property_label_off": _("Like"),
        "property_icon": "icon-thumbs-up",
    },

    "follow": {
        "property_tooltip_on": _("Stop following"),
        "property_tooltip_off": _("Follow"),
        "property_icon": "icon-plus",
    }
}

