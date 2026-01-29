#filchat.models.py
from django.db import models
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel

class FilChat(models.Model):
    file = models.FileField(upload_to='uploads/')
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class FilChatPage(Page):
    template = "filchat/filchat_page.html"
    content_panels = Page.content_panels
