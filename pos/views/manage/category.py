from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Category
from pos.views.util import JSON_response, JSON_error, JSON_parse, JSON_ok, resize_image, validate_image, \
    image_dimensions, max_field_length, image_from_base64, has_permission, no_permission_view
from common import globals as g


########################
### helper functions ###
########################
def category_breadcrumbs(category):
    # assemble the name in form category>subcategory>subsubcategory>...
    name = []
    
    while 1:
        name.append(category.name)
        category = category.parent
        if not category:
            break
        
    # reverse and join
    name.reverse()
    name = ' > '.join(name)
    
    return name


def category_to_dict(c):
    if c.parent:
        parent_id = c.parent.id
    else:
        parent_id = None

    r = {
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'parent_id': parent_id,
        'image': "",
    }

    if c.image:
        r['image'] = c.image.url

    return r


def validate_category(user, company, data):
    # data format (*-validation needed):
    # id
    # name*
    # description
    # image
        
    def r(status, msg):
        return {'status':status,
            'data':data,
            'message':msg}

    # return:
    # {status:true/false - if cleaning succeeded
    #  data:cleaned_data - empty dict if status = false
    #  message:error_message - empty if status = true
    
    try:
        data['id'] = int(data['id'])
    except:
        # this shouldn't happen
        return r(False, _("Wrong product id"))
    
    if data['id'] != -1:
        # check if product belongs to this company and if he has the required permissions
        try:
            p = Category.objects.get(id=data['id'], company=company)
        except Category.DoesNotExist:
            return r(False, _("Cannot edit product: it does not exist"))
        
        if p.company != company or not has_permission(user, company, 'product', 'edit'):
            return r(False, _("You have no permission to edit this product"))
    
    # parent
    parent_id = data['parent_id']
    if parent_id != -1:
        # check if product belongs to this company and if he has the required permissions
        try:
            p = Category.objects.get(id=parent_id, company=company)
        except Category.DoesNotExist:
            return r(False, _("Cannot edit product: parent id does not exist"))
        
        if p.company != company or not has_permission(user, company, 'product', 'edit'):
            return r(False, _("You have no permission to edit this product"))
    
    # name
    if not data['name']:
        return r(False, _("No name entered"))
    elif len(data['name']) > max_field_length(Category, 'name'):
        return r(False, _("Name too long"))
    else:
        if data['id'] == -1: # when adding new products:
            # check if a product with that name exists
            p = Category.objects.filter(company=company,name=data['name'])
            if p.count() > 0:
                return r(False,
                    _("There is already a product with that name") +  \
                    " (" + _("code") + ": " + p[0].code + ")")
    data['name'] = data['name'].strip()
    

    # image:
    if data['change_image'] == True:
        if 'image' in data: # new image has been uploaded
            data['image'] = image_from_base64(data['image'])
            if not data['image']:
                # something has gone wrong during conversion
                return r(False, _("Image upload failed"))
        else:
            # image will be deleted in view
            pass
    else:
        # no change regarding images
        data['image'] = None
    
    # description, notes - anything can be entered
    data['description'] = data['description'].strip()
        
    return {'status':True, 'data':data} 


def get_all_categories(company_id, category_id=None, sort='name', data=None, level=0, json=False):
    """ return a 'flat' list of all categories (converted to dictionaries/json) """
    
    #def category_to_dict(c, level): # c = Category object # currently not needed
    #    return {'id':c.id,
    #            'name':c.name,
    #            'description':c.description,
    #            'image':c.image,
    #            'level':level
    #    }

    if data is None:
        data = []

    if category_id:
        c = Category.objects.get(company__id=company_id, id=category_id)
        # add current category to list
        c.level = level
        #data.append(category_to_dict(c, level))
        # if json == true, add to dictionary rather than queryset
        if json:
            entry = category_to_dict(c) 
            entry['level'] = c.level  # some additional data
            entry['breadcrumbs'] = category_breadcrumbs(c)
            data.append(entry)
        else:
            data.append(c)
        
        # append all children
        children = Category.objects.filter(company__id=company_id, parent__id=category_id).order_by(sort)
        level += 1
        for c in children:
            get_all_categories(company_id, c.id, data=data, level=level, sort=sort, json=json)
    else:
        cs = Category.objects.filter(company__id=company_id, parent=None).order_by(sort)
        for c in cs:
            get_all_categories(c.company.id, c.id, data=data, level=level, sort=sort, json=json)

    return data


def get_subcategories(category_id, sort='name', data=None):
    """ return a 'flat' list of all subcategories' ids """
    if data is None:
        data = []

    c = Category.objects.get(id=category_id)
    data.append(c.id)
        
    # append all children
    children = Category.objects.filter(parent__id=category_id).order_by(sort)
    for c in children:
        get_subcategories(c.id, data=data, sort=sort)
    
    return data


def get_all_categories_structured(company, category=None, data=None, sort='name', level=0):
    """ return a structured list of all categories of given company """
    if data is None:
        data = []

    if not category:
        # list all categories that have no parent
        category = Category.objects.filter(company=company, parent=None).order_by(sort)
        
        for c in category:
            data.append(get_all_categories_structured(company, c, data, sort, 0))
            
        return data
    else:
        # add current category to list
        current = category_to_dict(category)
        level += 1
        current['level'] = level
        current['children'] = []  # will contain subcategories
        
        # list all categories with this parent
        children = Category.objects.filter(company=company, parent=category).order_by(sort)
        
        # add them to the list
        for c in children:
            current['children'].append(get_all_categories_structured(company, c, level=level))

    return current


#############
### views ###
#############
@login_required
def web_JSON_categories(request, company):
    return JSON_categories(request, company)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_categories(request, company):
    print JSON_categories(request, company)
    return JSON_categories(request, company)


def JSON_categories(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # permissions
    if not has_permission(request.user, c, 'category', 'list'):
        return JSON_error("no permission")
    
    # return all categories' data in JSON format
    return JSON_response(get_all_categories(c.id, sort='name', data=[], json=True))

class CategoryForm(forms.ModelForm):
    # take special case of urls
    def clean_image(self):
        return validate_image(self)

    class Meta:
        model = Category
        fields = ['name',
                  'description',
                  'image']
    
@login_required
def list_categories(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least guest to view
    if not has_permission(request.user, c, 'category', 'list'):
        return no_permission_view(request, c, _("view categories"))
    
    context = {
        'company':c,
        'categories':get_all_categories(c.id, data=[]),
        'title':_("Categories"),
        'site_title':g.MISC['site_title'],
        'image_dimensions':image_dimensions('thumb_small'),
    }
    
    return render(request, 'pos/manage/categories.html', context)



@login_required
def web_add_category(request, company, parent_id=-1):
    return add_category(request, company, parent_id)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_add_category(request, company):
    return m_add_category(request, company, -1)


def m_add_category(request, company, parent_id=-1):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can add category
    if not has_permission(request.user, c, 'category', 'edit'):
        return JSON_error(_("You have no permission to add products"))

    data = JSON_parse(request.POST['data'])
    
    # validate data
    valid = validate_category(request.user, c, data, parent_id)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
        
    if int(parent_id) == -1:
        parent = None
    else:
        parent = Category.objects.get(id=parent_id)
    
    # save category:
    product = Category(
        company = c,
        parent = parent,
        name = data['name'],
        description = data['description'],
        created_by = request.user,
    )
    product.save()
    
    # add image, if it's there
    if data['change_image']:
        if 'image' in data:
            product.image = data['image']
            product.save()
    
    return JSON_ok()

def add_category(request, company, parent_id):
    # get company
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'category', 'edit'):
        return no_permission_view(request, c, _("add categories"))
    
    # if parent_id == -1, this is a top-level category
    parent_id = int(parent_id)
    if parent_id == -1:
        parent = None
    else:
        parent = get_object_or_404(Category, id=parent_id)
        if parent.company != c:
            raise Http404
    
    context = {
        'company':c,
        'parent_id':parent_id,
        'add':True,
        'image_dimensions':image_dimensions('category'),
        'title':_("Add category"),
        'site_title':g.MISC['site_title']
    }
    
    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES) # instance = None
        
        if form.is_valid():
            # created_by and company_id (only when creatine a new category)
            category = form.save(False)
            category.parent = parent
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = c.id
        
            form.save()

            if category.image:
                resize_image(category.image.path, g.IMAGE_DIMENSIONS['category'])
            
            return redirect('pos:list_categories', company=c.url_name)
    else:
        form = CategoryForm() # create a new category
        
    context['form'] = form

    return render(request, 'pos/manage/category.html', context)

@login_required
def web_edit_category(request, company, category_id):
    return edit_category(request, company, category_id)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_edit_category(request, company, category_id):
    return m_edit_category(request, company, category_id)

def m_edit_category(request, company, category_id):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can edit product
    if not has_permission(request.user, c, 'category', 'edit'):
        return JSON_error(_("You have no permission to edit products"))

    data = JSON_parse(request.POST['data'])

    # see if product exists in database
    try:
        category = Category.objects.get(id=category_id)
    except:
        return JSON_error(_("Product does not exist"))
    
    # validate data
    valid = validate_category(request.user, c, data, category_id)
    
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    # update category:
    category.name = data['name']
    category.description = data['description']
    

    # image
    if data['change_image'] == True:
        if data['image']: # new image is uploaded
            # create a file from the base64 data and save it to product.image
            if category.image:
                category.image.delete()
            # save a new image
            category.image = data['image'] # conversion from base64 is done in validate_product
        else: # delete the old image
            category.image.delete()
    category.save()
    return JSON_ok()

def edit_category(request, company, category_id):
    c = get_object_or_404(Company, url_name=company)
    
    # get category
    category = get_object_or_404(Category, id=category_id)
    # check if category actually belongs to the given company
    if category.company != c:
        raise Http404 # this category does not exist for the current user
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'category', 'edit'):
        return no_permission_view(request, c, _("edit categories"))
    
    context = {'company':c, 'category_id':category_id}
    
    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES, instance=category)
        
        if form.is_valid():
            # created_by and company_id (only when creatine a new category)
            category = form.save(False)
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = c.id
        
            form.save()
            if category.image:
                resize_image(category.image.path, g.IMAGE_DIMENSIONS['category'])
            
            return redirect('pos:list_categories', company=c.url_name)
    else:
        if category:
            form = CategoryForm(instance=category) # update existing category
        else:
            form = CategoryForm() # create a new category
        
    context['form'] = form
    context['company'] = c
    context['category'] = category
    context['image_dimensions'] = g.IMAGE_DIMENSIONS['category']
    context['title'] = _("Edit category")
    context['site_title'] = g.MISC['site_title']
    
    return render(request, 'pos/manage/category.html', context)

@login_required
def web_delete_category(request, company, category_id):
    return delete_category(request, company, category_id)


def delete_category(request, company, category_id):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'category', 'edit'):
        return no_permission_view(request, c, _("delete categories"))
    
    # get category
    category = get_object_or_404(Category, id=category_id)
    # check if category actually belongs to the given company
    if category.company != c:
        raise Http404 # this category does not exist for the current user

    if Category.objects.filter(parent=category).count() > 0:
        return JSON_error("Cannot delete category with subcategories")

    # delete the category and return to management page
    try:
        category.delete()
    except:
        pass
    
    return redirect('pos:list_categories', company=c.url_name)


def get_category(request, company, category_id):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # permissions: needs to be guest to view products
    if not has_permission(request.user, c, 'product', 'list'):
        return JSON_error(_("You have no permission to view products"))
    
    category = get_object_or_404(Category, id = category_id, company = c)
    
    return JSON_response(category_to_dict(category))

