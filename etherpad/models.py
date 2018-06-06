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
    server_api_url = "http://localhost:9001/api"
    server_apikey = "5a8e9ba6172d91c6520c7d67d46a0b4600b1ed5ff02ec514b9946c471510984e"
    # group = models.ForeignKey(Group)
    groupID = "g.0iZ2zvCqPNpJ7qBp"


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
