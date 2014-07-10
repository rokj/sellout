import Image
from StringIO import StringIO
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from common.images import image_from_base64, resize_image

from pos.models import Company

from pos.views.util import JSON_response, JSON_parse, has_permission, no_permission_view, JSON_ok, JSON_error, \
    max_field_length

from common import globals as g
import unidecode
from common.functions import get_random_string, get_terminal_url

import re
import os


###
### helper functions etc
###
def is_url_name_unique(url_name):
    return not Company.objects.filter(url_name=url_name).exists()


def check_url_name(url_name):
    # a valid url name:
    # 1. must not be equal to g.MISC['management_url']
    if url_name == g.MISC['management_url']:
        return False
    
    #  2. length between 1 and max_len
    #  3. allowed characters: alphanumeric and dash
    #  4. must not begin or end with dash
    rem = re.match('^\w\w*(?:-\w+)*$', url_name)
    try:
        if rem.group(0) == url_name:
            #  5. must be unique within the database
            if is_url_name_unique(url_name):
                return True
            else:
                return False
        else:
            return False
    except:
        return False


def unique_url_name(url_name):
    # check if url exists already and if it does, append a number
    # and return a unique url.
    
    max_len = g.MISC['company_url_length']
    # first, check for length
    if len(url_name) > max_len:
        url_name = url_name[0:max_len]
    
    # if there's already a url_name entry in database, return url_name-n, the first available name
    n = 1
    try_name = url_name
    while True:
        if is_url_name_unique(try_name):
            return try_name
        else:
            try_name = url_name[0:max_len - 1 - len(str(n))] + '-' + str(n)
            n += 1


def url_name_suggestions(request):
    # there's a 'name' in request:
    # take it and return a list of a few company url suggestions
    suggestions = []
    
    try:  # get name from sent data
        name = JSON_parse(request.POST.get('data'))['name']
    except:
        return JSON_response({'suggestions':[]})
    
    # 0. "lowercaseize"
    name = name.lower()
    
    # 1. "asciify"
    s = unidecode.unidecode(name)
    
    # 2. remove forbidden characters (everything but alphanumeric and dash) ("alphanumerify")
    s = re.sub(r'[^\w-]', ' ', s).strip()
    
    # first suggestion: full name - also remove duplicate -'s
    suggestions.append(unique_url_name(re.sub(r' +', '-', s)))
    
    # 2. remove one-character words ("unonecharacterify")
    # regex: one character followed by a space at the beginning OR
    # space followed by a character followed by a space OR
    # space followed by a character at the end
    s = re.sub(r'(^. )|(( ).(?= ))|( .$)', ' ', s)
    
    # 3. suggestions:
    # first word, then first and second, then ..., up to g.MISC['company_url_length'] chars
    max_len = g.MISC['company_url_length']
    words = s.split()
    
    for w in range(1, len(words)+1):
        s = ''
        for i in range(w):
            s += '-' + words[i]
            
        s = s[1:]  # cut off the first '-'
        if len(s) >= max_len:
            break
        
        suggestions.append(unique_url_name(s))
    
    # only first characters of every word (a.k.a. acronym)
    s = ''
    for w in words:
        s += w[0]
    suggestions.append(unique_url_name(s))

    # 4. remove possible inapropriate suggestions
    valid = []
    for s in suggestions:
        if check_url_name(s):
            valid.append(s)
    
    # 5. remove duplicates
    valid = list(set(valid))
    
    # 6. sort by length
    valid.sort(key=len)
    suggestions = valid
    del valid
    
    # 3a. add a random string to suggestions
    suggestions.append(unique_url_name(get_random_string(length=5).lower()))
    
    # pass on to the page
    return JSON_response({'suggestions':suggestions})


###############
### company ###
###############
class CompanyForm(forms.ModelForm):
    # take special care of urls
    def clean_url_name(self):
        url_name = self.cleaned_data['url_name']
        
        if 'url_name' in self.initial:
            initial_url_name = self.initial['url_name']
        else:
            initial_url_name = ""
            
        if url_name == initial_url_name:
            return url_name
        
        if not check_url_name(url_name):
            raise forms.ValidationError(_("Url of the company is invalid or exists already."))
        else:
            return url_name

    class Meta:
        model = Company
        fields = [#'color_logo',  # logos have been left out and moved to separate forms (html only)
                  #'monochrome_logo',
                  'name',
                  'url_name',
                  'email',
                  'street',
                  'postcode',
                  'city',
                  'state',
                  'country',
                  'phone',
                  'vat_no',
                  'notes',
                  'website']
        #widgets = {
        #    'color_logo': widgets.PlainClearableFileInput,
        #    'monochrome_logo': widgets.PlainClearableFileInput,
        #}


def validate_company(user, company, data):

    def r(status, msg):
        return {'status': status,
                'data': data,
                'message': msg}

    if not has_permission(user, company, 'company', 'edit'):
        return r(False, _("You have no permission to edit this company"))

    if data.get('url_name'):
        url_name = data['url_name']
        if url_name != company.url_name:
            if not check_url_name(url_name):
                return r(False, _("Url of the company is invalid or exists already."))
    else:
        url_name = company.url_name

    print data

    if not data.get('name'):
        return r(False, _("No name entered"))
    elif len(data['name']) > max_field_length(Company, 'name'):
        return r(False, _("Name too long"))

    if not data.get('email'):
        return r(False, _("No email entered"))

    return {'status':  True, 'data': data}


# for json etc.
def company_to_dict(company, android=False):
    c = {}

    c['name'] = company.name
    c['url_name'] = company.url_name
    c['email'] = company.email
    c['street'] = company.street
    c['postcode'] = company.postcode
    c['city'] = company.city
    c['state'] = company.state
    c['country'] = company.country.name
    c['phone'] = company.phone
    c['vat_no'] = company.vat_no
    c['website'] = company.website
    c['notes'] = company.notes

    if company.color_logo:
        c['color_logo_url'] = company.color_logo.url
    else:
        c['color_logo_url'] = None

    if company.monochrome_logo:
        c['monochrome_logo_url'] = company.monochrome_logo.url
    else:
        c['monochrome_logo_url'] = None

    return c


# registration
@login_required
def register_company(request):
    # permissions: anybody can register a company
    
    # show CompanyForm, empty
    if request.method == 'POST':
        # submit data
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(False)
            company.created_by = request.user
            form.save()
            
            # continue with registration
            
            # TODO: add 'admin' permissions for newly registered company to request.user
            return redirect('pos:terminal', company=form.cleaned_data['url_name'])  # home page
    else:
        # show an empty form
        form = CompanyForm()

    context = {
        'form': form,
        'pos_url': get_terminal_url(request),
        'color_logo_dimensions': g.IMAGE_DIMENSIONS['color_logo'],
        'monochrome_logo_dimensions': g.IMAGE_DIMENSIONS['monochrome_logo'],
        'max_upload_size': g.MISC['max_upload_image_size'],

        'title': _("Registration"),
        'site_title': g.MISC['site_title'],
    }

    return render(request, 'pos/manage/registration.html', context)

# edit after registration
@login_required
def edit_company(request, company):
    # get company, it must exist
    c = get_object_or_404(Company, url_name=company)
        
    # check if the user has permission to change it
    # only admins can change company details
    if not has_permission(request.user, c, 'company', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit company details."))
    
    context = {
        'company': c,
        'color_logo_dimensions': g.IMAGE_DIMENSIONS['color_logo'],
        'monochrome_logo_dimensions': g.IMAGE_DIMENSIONS['monochrome_logo'],
        'max_upload_size': g.MISC['max_upload_image_size'],

        'title': _("Company details"),
        'site_title': g.MISC['site_title'],
        'pos_url': get_terminal_url(request),
    }
    
    if request.method == 'POST':
        # submit data
        form = CompanyForm(request.POST, request.FILES, instance=c)
        
        if form.is_valid():
            form.save()

            # for an eventual message for the user
            context['saved'] = True
            # if url_name was changed, redirect to new address
            return redirect('pos:edit_company', company=c.url_name)
    else:
        form = CompanyForm(instance=c)
        
    context['form'] = form

    return render(request, 'pos/manage/company.html', context)


@login_required
def upload_color_logo(request, company):
    # Kudos: https://snipt.net/danfreak/generate-thumbnails-in-django-with-pil/
    c = Company.objects.get(url_name=company)

    data = JSON_parse(request.POST.get('data'))

    if 'image' in data:
        # read the new image and upload it
        image_file = image_from_base64(data.get('image'))

        if not image_file:
            return JSON_error(_("No file sent"))

        resize = False

        # resize and convert image if necessary
        color_logo = Image.open(image_file)

        if color_logo.mode not in ('L', 'RGB'):
            # Kudos: http://stackoverflow.com/questions/9166400/convert-rgba-png-to-rgb-with-pil
            # create a white image the same size as color_logo
            color_logo.load()

            background = Image.new("RGB", color_logo.size, (255, 255, 255))
            background.paste(color_logo, mask=color_logo.split()[3]) # 3 is the alpha channel

            color_logo = background
            color_logo = color_logo.convert('RGB')


        if color_logo.size != g.IMAGE_DIMENSIONS['color_logo']:
            # the logo has wrong dimensions
            resize = True

        if color_logo.format != g.MISC['image_format']:
            # the logo is not in the correct format
            resize = True

        if resize:
            color_logo = resize_image(color_logo, g.IMAGE_DIMENSIONS['color_logo'], 'fit')

        if c.color_logo.name:
            # the logo exists already, delete it
            try:
                os.remove(c.color_logo.path)
            except (OSError, ValueError):
                pass

        temp_handle = StringIO()
        color_logo.save(temp_handle, 'png')
        temp_handle.seek(0)

        # Save to the thumbnail field
        suf = SimpleUploadedFile('temp', temp_handle.read(), ('image/'+g.MISC['image_format']).lower())

        c.color_logo.save(suf.name + '.png', suf, save=False)
        c.save()

        return JSON_response({'status': 'ok', 'logo_url': c.color_logo.url})
    else:
        # there is no image, remove the existing one
        try:
            os.remove(c.color_logo.path)
            c.color_logo.delete()
            c.save()
        except (OSError, ValueError):
            pass

        return JSON_ok()


@login_required
def upload_monochrome_logo(request, company):
    c = Company.objects.get(url_name=company)

    data = JSON_parse(request.POST.get('data'))

    print data

    if 'image' in data:
        # read the new image and upload it
        image_file = image_from_base64(data.get('image'))

        if not image_file:
            return JSON_error(_("No file sent"))

        resize = False

        # resize and convert image if necessary
        monochrome_logo = Image.open(image_file)

        if monochrome_logo.size != g.IMAGE_DIMENSIONS['monochrome_logo']:
            # the logo has wrong dimensions
            resize = True

        if monochrome_logo.format != g.MISC['image_format']:
            # the logo is not in the correct format
            resize = True

        # resize first
        if resize:
            monochrome_logo = resize_image(monochrome_logo, g.IMAGE_DIMENSIONS['monochrome_logo'], 'fit')

        # then convert to monochrome
        if monochrome_logo.mode != '1':
            monochrome_logo = monochrome_logo.convert('1')

        if c.monochrome_logo.name:
            # the logo exists already, delete it
            try:
                os.remove(c.monochrome_logo.path)
            except (OSError, ValueError):
                pass

        temp_handle = StringIO()
        monochrome_logo.save(temp_handle, 'png')
        temp_handle.seek(0)

        # Save to the thumbnail field
        suf = SimpleUploadedFile('temp', temp_handle.read(), ('image/' + g.MISC['image_format']).lower())

        c.monochrome_logo.save(suf.name + '.png', suf, save=False)
        c.save()

        return JSON_response({'status': 'ok', 'logo_url': c.monochrome_logo.url})
    else:
        # there is no image, remove the existing one
        try:
            os.remove(c.monochrome_logo.path)
            c.monochrome_logo.delete()
            c.save()
        except (OSError, ValueError):
            pass

        return JSON_ok()


@login_required
def create_monochrome_logo(request, company):
    c = Company.objects.get(url_name=company)

    if not c.color_logo:
        return False

    # get company's color logo
    color_logo = Image.open(c.color_logo.path)

    # resize it to monochrome_logo dimension
    black_logo = color_logo.copy()
    black_logo.thumbnail(g.IMAGE_DIMENSIONS['monochrome_logo'], Image.ANTIALIAS)
    # reduce color depth
    black_logo = black_logo.convert(mode='1')
    # create a new path for the monochrome logo
    new_path = os.path.splitext(c.color_logo.path)[0]
    new_path = new_path + '_monochrome.' + g.MISC['image_format']
    # save to the new path
    black_logo.save(new_path, g.MISC['image_format'], bits=1)

    # save to stupid django field
    django_file = File(open(new_path))
    c.monochrome_logo.save('new', django_file)
    django_file.close()

    # return an url to the new logo
    return JSON_response({'status': 'ok', 'logo_url': c.monochrome_logo.url})