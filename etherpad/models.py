from django.db import models
from django.db.models.signals import pre_delete
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

from py_etherpad import EtherpadLiteClient

import string
import random

# Create your models here.
class Pad(models.Model):
    """Schema and methods for etherpad-lite pads
    """
    name = models.CharField(max_length=256)
    server_api_url = models.URLField(max_length= 256, verbose_name= _('URL'))
    server_apikey = models.CharField(max_length=256, verbose_name=_('API key'))
    # group = models.ForeignKey(Group)
    groupID = models.CharField(max_length=256, blank= True)


    def __str__(self):
        return self.name

    @property
    def padid(self):
        return "%s" % self.name

    @property
    def epclient(self):
        return EtherpadLiteClient(self.server_apikey, self.server_api_url)

    def Create(self):
        return self.epclient.createGroupPad(self.groupID, self.name)

    def Destroy(self):
        return self.epclient.deletePad(self.padid)

    def isPublic(self):
        result = self.epclient.getPublicStatus(self.padid)
        return result['publicStatus']

    def ReadOnly(self):
        return self.epclient.getReadOnlyID(self.padid)

    def save(self, *args, **kwargs):
        self.Create()
        super(Pad, self).save(*args, **kwargs)   


def padDel(sender, **kwargs):
    """Make sure pads are purged from the etherpad-lite server on deletion
    """
    pad = kwargs['instance']
    pad.Destroy()
pre_delete.connect(padDel, sender=Pad)
