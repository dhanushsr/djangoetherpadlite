from django.contrib import admin
from etherpad.models import *
# Register your models here.
admin.site.register(PadAuthor)
admin.site.register(PadServer)
admin.site.register(Pad)
admin.site.register(PadGroup)