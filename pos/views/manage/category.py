from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404, HttpResponseRedirect, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Category, Product
from pos.views.util import JsonError, JsonParse, JsonOk,  \
    max_field_length, has_permission, no_permission_view, JsonStringify

from common import globals as g

import random

########################
### helper functions ###
########################
def category_to_dict(c, android=False):
    if c.parent:
        parent_id = c.parent.id
    else:
        parent_id = None

    r = {
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'parent_id': parent_id,

        'color': c.color,
        'breadcrumbs': c.breadcrumbs['name'],
        'path': c.breadcrumbs['id'],
    }

    if not android:
        r['add_child_url'] = reverse('pos:add_category', kwargs={'company': c.company.url_name, 'parent_id': c.id})
        r['edit_url'] = reverse('pos:edit_category', kwargs={'company': c.company.url_name, 'category_id': c.id})
    else:
        r['product_cunt'] = c.product_count
        r['level'] = c.category_level

    return r


def validate_category(user, company, data):
    # data format (*-validation needed):
    # id
    # name*
    # description

    def r(status, msg):
        return {'status': status,
            'data': data,
            'message': msg}

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

        # don't allow adding children as parent when editing
        if data['id'] != -1:
            c = Category.objects.get(id=data['id'])

            if c.id == parent_id:
                return r(False, _("Category cannot be parent of it self"))

            if not validate_parent(c, parent_id):
                return r(False, _("Cannot set child as parent"))





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
                    _("There is already a category with that name") +
                    " (" + _("code") + ": " + p[0].name + ")")
    data['name'] = data['name'].strip()

    # description, notes - anything can be entered
    data['description'] = data['description'].strip()

    return {'status': True, 'data': data}


def validate_parent(category, parent_id):
    categories = Category.objects.filter(parent=category)
    for c in categories:
        if c.id == parent_id:
            return False
        else:
            validate_parent(c, parent_id)
    return True


def get_all_categories(company, category=None, sort='name', data=None, level=0, json=False):
    """ return a 'flat' list of all categories (converted to dictionaries/json) """

    #def category_to_dict(c, level): # c = Category object # currently not needed
    #    return {'id':c.id,
    #            'name':c.name,
    #            'description':c.description,
    #            'level':level
    #    }

    if data is None:
        data = []

    if category:
        c = category
        # add current category to list
        c.level = level
        #data.append(category_to_dict(c, level))
        # if json == true, add to dictionary rather than queryset
        if json:
            entry = category_to_dict(c)
            entry['level'] = c.level  # some additional data
            entry['breadcrumbs'] = c.breadcrumbs['name']
            entry['path'] = c.breadcrumbs['id']
            data.append(entry)
        else:
            data.append(c)

        # append all children
        children = Category.objects.filter(company=company, parent=category).order_by(sort)
        level += 1
        for c in children:
            get_all_categories(company, c, data=data, level=level, sort=sort, json=json)
    else:
        cs = Category.objects.filter(company=company, parent=None).order_by(sort)
        for c in cs:
            get_all_categories(c.company, c, data=data, level=level, sort=sort, json=json)

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


def get_all_categories_structured(company, category=None, data=None, sort='name', level=0, android=False):
    """ return a structured list of all categories of given company """
    if data is None:
        data = []

    if not category:
        # list all categories that have no parent
        category = Category.objects.filter(company=company, parent=None).order_by(sort)

        for c in category:
            data.append(get_all_categories_structured(company, c, data, sort, 0, android=android))

        return data
    else:
        # add current category to list
        current = category_to_dict(category, android)
        level += 1
        current['level'] = level
        current['children'] = []  # will contain subcategories

        # list all categories with this parent
        children = Category.objects.filter(company=company, parent=category).order_by(sort)

        # add them to the list
        for c in children:
            current['children'].append(get_all_categories_structured(company, c, level=level, android=android))

    return current


#############
### views ###
#############
@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_categories(request, company):
    return JSON_categories(request, company)


@login_required
def JSON_categories(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'category', 'view'):
        return JsonError("no permission")

    # return all categories' data in JSON format
    return JsonResponse(get_all_categories(c, sort='name', data=[], json=True))


class CategoryForm(forms.ModelForm):
    # take special case of urls
    class Meta:
        model = Category
        fields = ['parent',
                  'name',
                  'description',
                  'color']
        widgets = {
            'color': forms.HiddenInput
        }


@login_required
def list_categories(request, company):
    c = get_object_or_404(Company, url_name=company)

    # check permissions
    if not has_permission(request.user, c, 'category', 'view'):
        return no_permission_view(request, c, _("You have no permission to view categories."))

    context = {
        'box_dimensions': g.IMAGE_DIMENSIONS['category'],
        'company': c,
        'categories': JsonStringify(get_all_categories_structured(c), True),
        'title': _("Categories"),
        'site_title': g.MISC['site_title'],
    }

    return render(request, 'pos/manage/categories.html', context)


@login_required
def add_category(request, company, parent_id=-1):
    # get company
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'category', 'edit'):
        return no_permission_view(request, c, _("You have no permission to add categories."))

    # if parent_id == -1, this is a top-level category
    try:
        parent_id = int(parent_id)
        if parent_id == -1:
            parent = None
            color = random.choice(g.CATEGORY_COLORS)
        else:
            parent = Category.objects.get(id=parent_id)
            color = parent.color

            # check if not adding to some other company's category
            if parent.company != c:
                return no_permission_view(request, c, _("You have no permission to add to this category."))
    except Category.DoesNotExist:
        raise Http404
    except:
        parent = None
        color = g.CATEGORY_COLORS[0]

    context = {
        'company': c,
        'parent': parent,
        'add': True,
        'colors': JsonStringify(g.CATEGORY_COLORS),
        'title': _("Add category"),
        'site_title': g.MISC['site_title']
    }

    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES)  # instance = None

        if form.is_valid():
            # created_by and company_id (only when creatine a new category)
            category = form.save(False)
            category.parent = parent
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = c.id

            form.save()

            # return to categories and select the just added category
            return HttpResponseRedirect(
                reverse('pos:list_categories', kwargs={'company': c.url_name}) + "#" + str(category.id))

    else:
        # create a new category (select parent and its color if adding child)
        form = CategoryForm(initial={'parent': parent_id, 'color': color})

    context['form'] = form

    return render(request, 'pos/manage/category.html', context)


@login_required
def edit_category(request, company, category_id):
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'category', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit categories."))

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise Http404

    # check if category actually belongs to the given company
    if category.company != c:  # "you have no permission to edit this category"
        raise Http404

    context = {'company': c, 'category_id': category_id}

    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES, instance=category)

        if form.is_valid():
            # created_by and company_id (only when creating a new category)
            category = form.save(False)
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = c.id

            form.save()

            # return to categories and select the just added category
            return HttpResponseRedirect(
                reverse('pos:list_categories', kwargs={'company': c.url_name}) + "#" + str(category.id))
    else:
        if category:
            form = CategoryForm(instance=category)  # update existing category
        else:
            form = CategoryForm()  # create a new category

    context['form'] = form
    context['company'] = c
    context['category'] = category
    context['colors'] = JsonStringify(g.CATEGORY_COLORS)
    context['title'] = _("Edit category")
    context['site_title'] = g.MISC['site_title']

    return render(request, 'pos/manage/category.html', context)


@login_required
def delete_category(request, company):
    c = Company.objects.get(url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'category', 'edit'):
        return JsonError(_("You have no permission to delete categories"))
    
    # get category
    try:
        category_id = int(JsonParse(request.POST.get('data')).get('category_id'))
        category = Category.objects.get(id=category_id)
        # check if category actually belongs to the given company
        if category.company != c:
            return JsonError(_("You have no permission to delete this category"))
    except:
        return JsonError(_("No category specified"))

    if Category.objects.filter(parent=category).count() > 0:
        return JsonError(_("Cannot delete category with subcategories"))

    # do not delete a category with products
    if Product.objects.filter(category=category).exists():
        return JsonError(_("There are products in this category, it cannot be deleted"))

    # delete the category and return to management page
    try:
        category.delete()
    except:
        return JsonError(_("Category could not be deleted"))
    
    return JsonOk()


def get_category(request, company, category_id):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
    
    # permissions: needs to be guest to view products
    if not has_permission(request.user, c, 'product', 'view'):
        return JsonError(_("You have no permission to view products"))
    
    category = get_object_or_404(Category, id=category_id, company=c)
    
    return JsonResponse(category_to_dict(category))

