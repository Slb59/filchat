from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class CustomErrorPage(Page):
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    content = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('content'),
    ]

    # Empêcher cette page d'apparaître dans le menu de navigation ou les résultats de recherche
    show_in_menus_default = False

    def serve(self, request, *args, **kwargs):
        from django.shortcuts import render
        return render(request, "404.html", {
            'self': self,
            'request': request,
        }, status=404)


class Custom404Page(CustomErrorPage):
    ...

class Custom500Page(CustomErrorPage):
    ...

class Custom403Page(CustomErrorPage):
    ...