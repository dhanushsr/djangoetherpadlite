from django.shortcuts import render, get_object_or_404, redirect
import datetime
import time
import urllib
from urllib.parse import urlparse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.base import SessionBase
# additional imports
from py_etherpad import EtherpadLiteClient

# local imports
from etherpad.models import Pad, PadGroup, PadServer, PadAuthor
from etherpad import forms
from etherpad import config


@login_required
def home(request):
    return redirect('profile')

@login_required
def padCreate(request, pk):
    """Create a named pad for the given group
    """
    group = get_object_or_404(PadGroup, pk=pk)

    if request.method == 'POST':  # Process the form
        form = forms.PadCreate(request.POST)
        if form.is_valid():
            pad = Pad(
                name=form.cleaned_data['name'],
                server=group.server,
                group=group
            )
            pad.save()
            profile(request)
            return redirect('profile')
    else:  # No form to process so create a fresh one
        form = forms.PadCreate({'group': group.groupID})

    con = {
        'form': form,
        'pk': pk,
        'title': _('Create pad in %(grp)s') % {'grp': group.__unicode__()}
    }
    return render(request, 'padCreate.html', con)


@login_required
def padDelete(request, pk):
    """Delete a given pad
    """
    pad = get_object_or_404(Pad, pk=pk)

    # Any form submissions will send us back to the profile
    if request.method == 'POST':
        if 'confirm' in request.POST:
            pad.delete()
        return redirect('profile')

    con = {
        'action': '/etherpad/delete/' + pk + '/',
        'question': _('Really delete this pad?'),
        'title': _('Deleting  article %(pad)s') % {'pad': pad.__unicode__()}
    }
    return render(request, 'confirm.html', con)


@login_required
def groupCreate(request):
    """ Create a new Group
    """
    message = ""
    if request.method == 'POST':  # Process the form
        form = forms.GroupCreate(request.POST)
        if form.is_valid():
            group = form.save()
            # temporarily it is not nessessary to specify a server, so we take
            # the first one we get.
            server = PadServer.objects.all()[0]
            pad_group = PadGroup(group=group, server=server)
            pad_group.save()
            request.user.groups.add(group)
            return redirect('profile')
        else:
            message = _("This Groupname is allready in use or invalid.")
    else:  # No form to process so create a fresh one
        form = forms.GroupCreate()
    con = {
        'form': form,
        'title': _('Create a new Group'),
        'message': message,
    }
    return render( request, 'groupCreate.html',con)


@login_required
def groupDelete(request, pk):
    """
    """
    pass


@login_required
def profile(request):
    """Display a user profile containing etherpad groups and associated pads
    """
    name = str(request.user)

    try:  # Retrieve the corresponding padauthor object
        author = PadAuthor.objects.get(user=request.user)
    except PadAuthor.DoesNotExist:  # None exists, so create one
        author = PadAuthor(
            user=request.user,
            server=PadServer.objects.get(id=1)
        )
        author.save()
    author.GroupSynch()

    groups = {}
    for g in author.group.all():
        groups[g.__unicode__()] = {
            'group': g,
            'pads': Pad.objects.filter(group=g)
        }

    return render(request,'profile.html',
        {
            'name': name,
            'author': author,
            'groups': groups
        }
    )


# Create your views here.
@login_required
def pad(request, pk):
    """Create and session and display an embedded pad
    """

    # Initialize some needed values
    pad = get_object_or_404(Pad, pk=pk)
    padLink = pad.server.url + 'p/' + pad.group.groupID + '$' + \
        urllib.parse.quote_plus(pad.name)
    server = urlparse(pad.server.url)
    author = PadAuthor.objects.get(user=request.user)

    # if author not in pad.group.authors.all():
    #     return render(
    #         request,
    #         'pad.html',
    #         {
    #             'pad': pad,
    #             'link': padLink,
    #             'server': server,
    #             'uname': author.user.__unicode__(),
    #             'error': _('You are not allowed to view or edit this pad')
    #         }
    #     )
    # Create the session on the etherpad-lite side
    expires = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=config.SESSION_LENGTH
    )
    epclient = EtherpadLiteClient(pad.server.apikey, pad.server.apiurl)

    try:
        result = epclient.createSession(
            pad.group.groupID,
            author.authorID,
            time.mktime(expires.timetuple()).__str__()
        )
    except Exception as e:
        return render(request, 'pad.html', {'pad':pad, 'link': padLink, 'server':server, 'uname': author.user.__str__(), 'error': _('etherpad-lite session request returned:') + ' "' + str(e) + '"'})
    
    response = render(request, 'pad.html', {'pad': pad,'link': padLink,'server': server,'uname': author.user.__str__() ,'error': False} )

    # Delete the existing session first
    if ('padSessionID' in request.COOKIES):
        epclient.deleteSession(request.COOKIES['sessionID'])
        response.delete_cookie('sessionID', server.hostname)
        response.delete_cookie('padSessionID')

    # Set the new session cookie for both the server and the local site
    response.set_cookie(key = 'sessionID',value=result['sessionID'],expires=expires,httponly=False)
    response.set_cookie(key ='padSessionID',value=result['sessionID'],expires=expires,httponly=False)
    # request.session['sessionID']= result['sessionID']
    # request.session['padSessionID']= result['sessionID']
    # request.set_expiry(expires)
    return response