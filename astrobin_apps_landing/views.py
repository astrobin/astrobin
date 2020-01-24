from django.views.generic import TemplateView
from django.contrib.auth.models import User

from pybb.models import Post

from astrobin.models import Gear, Image

from nested_comments.models import NestedComment

class LandingView(TemplateView):
    template_name = "astrobin_apps_landing/landing.html"

    def get_context_data(self, **kwargs):
        context = super(LandingView, self).get_context_data(**kwargs)
        context["images"] = Image.all_objects.count()
        context["users"] = User.objects.count()
        context["comments"] = NestedComment.objects.count()
        context["posts"] = Post.objects.count()
        context["gear_items"] = Gear.objects.count()

        return context
