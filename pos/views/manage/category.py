# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: categories
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404

from pos.models import Company, Category
from pos.views.util import JSON_response, JSON_error, resize_image, validate_image, \
                           has_permission, no_permission_view, \
                           image_dimensions
from common import globals as g


from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated

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
    # get list: topmost category > sub > subsub > c
    # it's hard on database, but is only called once per terminal load or in management
    # NOT NEEDED
    #cid = [c.id]
    #cc = c;
    #while cc.parent:
    #    cc = cc.parent;
    #    cid.append(cc.id)
    #
    #cid.reverse()
    r = {
        'id':c.id,
        'name':c.name,
        'description':c.description,
        #'path':cid,
        'image':"",
    }
    if c.image:
        r['image'] = c.image.url
    return r


def get_all_categories(company_id, category_id=None, sort='name', data=[], level=0, json=False):
    
    """ return a 'flat' list of all categories (converted to dictionaries/json) """
    
    #def category_to_dict(c, level): # c = Category object # currently not needed
    #    return {'id':c.id,
    #            'name':c.name,
    #            'description':c.description,
    #            'image':c.image,
    #            'level':level
    #    }
    
    if category_id:
        c = Category.objects.get(company__id=company_id, id=category_id)
        # add current category to list
        c.level = level
        #data.append(category_to_dict(c, level))
        # if json == true, add to dictionary rather than queryset
        if json:
            entry = category_to_dict(c) 
            entry['level'] = c.level # some additional data
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

def get_all_categories_structured(company, category=None, data=[], sort='name'):
    """ return a structured list of all categories of given company """
    
    if not category:
        # list all categories that have no parent
        category = Category.objects.filter(company=company, parent=None).order_by(sort)
        
        for c in category:
            data.append(get_all_categories_structured(company, c, data, sort))
            
        return data
    else:
        # add current category to list
        current = category_to_dict(category)
        current['children'] = [] # will contain subcategories
        
        # list all categories with this parent
        children = Category.objects.filter(company=company, parent=category).order_by(sort)
        
        # add them to the list
        for c in children:
            current['children'].append(get_all_categories_structured(company, c))

    return current

#############
### views ###
#############
@login_required
def web_JSON_categories(request, company):
    return JSON_categories(request, company)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_categories(request,company):
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

def add_category(request, company, parent_id=-1):
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
    
    # delete the category and return to management page
    try:
        category.delete()
    except:
        pass
    
    return redirect('pos:list_categories', company=c.url_name)
