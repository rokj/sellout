from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from pos.models import Company, Discount
from common.functions import JsonError, has_permission, no_permission_view, format_number, format_date,\
    max_field_length, manage_delete_object, CompanyUserForm, CustomDateField, CustomDecimalField
from common import globals as g
import datetime as dtm
from config.functions import get_date_format, get_company_value


def discount_to_dict(user, company, d, android=False):
    ret = {
        'id': d.id,
        'description': d.description,
        'code': d.code,
        'type': d.type,
        'amount': format_number(user, company, d.amount, True),
        'enabled': d.enabled,
        'active': d.is_active,
    }

    if android and d.start_date:
        ret['start_date'] = [d.start_date.year, d.start_date.month, d.start_date.day]
    else:
        ret['start_date'] = format_date(user, company, d.start_date)

    if android and d.end_date:
        ret['end_date'] = [d.end_date.year, d.end_date.month, d.end_date.day]
    else:
        ret['end_date'] = format_date(user, company, d.end_date)
    return ret


@login_required
def json_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'discount', 'view'):
        return JsonError(_("You have no permission to view discounts"))

    return JsonResponse(get_all_discounts(request.user, c))


def get_all_discounts(user, company, android=False):
    """ returns all available discounts for this company in a list of dictionaries
        (see discount_to_dict for dictionary format)
    """
    discounts = Discount.objects.filter(company=company, enabled=True).order_by('code')

    ds = []
    for d in discounts:
        if d.is_active:
            ds.append(discount_to_dict(user, company, d, android))

    return ds


def validate_discount(data, user, company, android=False, discount=None):
    # validate for mobile, use forms
    if discount:
        form = DiscountForm(data=data, user=user, company=company, initial=discount_to_dict(user, company, discount))
    else:
        form = DiscountForm(data=data, user=user, company=company)

    if form.is_valid():

        if android:
            start_date = data.get('android_start_date')

            if start_date:
                start = dtm.date(year=start_date[0], month=start_date[1],
                                 day=start_date[2])
            else:
                start = None

            end_date = data.get('android_end_date')

            if end_date:
                end = dtm.date(year=end_date[0], month=end_date[1],
                                 day=end_date[2])
            else:
                end = None

            form.cleaned_data['start_date'] = start
            form.cleaned_data['end_date'] = end
            form.start_date = start
            form.end_date = end

        return {'status': True, 'message': None, 'form': form}
    else:
        message = form.errors.as_data().itervalues().next()[0].message
        return {'status': False, 'message': message, 'data': None}


#############
### views ###
#############
class DiscountForm(CompanyUserForm):
    id = forms.IntegerField(widget=forms.HiddenInput, required=False, initial=-1)
    description = forms.CharField(required=False, widget=forms.Textarea, max_length=max_field_length(Discount, 'description'))
    code = forms.CharField(required=True, max_length=max_field_length(Discount, 'code'))
    type = forms.ChoiceField(choices=g.DISCOUNT_TYPES, required=True)
    # this should be decimal, but we're formatting it our way
    amount = CustomDecimalField(required=True)
    # this should be date...
    start_date = CustomDateField(required=False)
    end_date = CustomDateField(required=False)
    enabled = forms.BooleanField(required=False,
                                 widget=forms.Select(choices=((True, _("Yes")), (False, _("No")))))

    def clean_code(self):
        try:
            discount = Discount.objects.get(company=self.company, code=self.cleaned_data.get('code'))

            # if ids match, the discount is being edited; if a discount with this code has been found and
            # it's the same discount that's being edited, that's fine
            if discount.id != self.cleaned_data.get('id'):
                raise ValidationError(_("Discount with this code already exists"))
            else:
                return self.cleaned_data.get('code')
        except Discount.DoesNotExist:
            return self.cleaned_data.get('code')


class DiscountFilterForm(CompanyUserForm):
    search = forms.CharField(label=_("Search text"), required=False)
    start_date = CustomDateField(required=False, max_length=g.DATE['max_date_length'])
    end_date = CustomDateField(required=False, max_length=g.DATE['max_date_length'])
    enabled = forms.NullBooleanField(required=False)

    page = forms.IntegerField(widget=forms.HiddenInput, initial=1)


@login_required
def list_discounts(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'discount', 'view'):
        return no_permission_view(request, c, _("You have no permission to view discounts."))
    
    N = 6
    searched = False

    # show the filter form
    form = DiscountFilterForm(data=request.GET, user=request.user, company=c)

    if form.is_valid():
        discounts = Discount.objects.filter(company__id=c.id)

        # filter by whatever is in the form: description
        if form.cleaned_data.get('search'):
            discounts = discounts.filter(description__icontains=form.cleaned_data['search']) | \
                        discounts.filter(code__icontains=form.cleaned_data['search'])

        # start_date
        t = form.cleaned_data.get('start_date')
        if t:
            discounts = discounts.filter(start_date__gte=t)

        # end_date
        t = form.cleaned_data.get('end_date')
        if t:
            discounts = discounts.filter(start_date__gte=t)

        # enabled
        t = form.cleaned_data.get('enabled')
        if t is not None:
            discounts = discounts.filter(enabled=t)

        page = form.cleaned_data.get('page')
        searched = True  # search results are being displayed
    else:
        form = DiscountFilterForm(user=request.user, company=c)
        discounts = Discount.objects.filter(company=c)[:N]
        page = 1

    paginator = Paginator(discounts, g.MISC['discounts_per_page'])
    if page:
        discounts = paginator.page(page)
    else:
        discounts = paginator.page(1)

    context = {
        'company': c,

        'discounts': discounts,
        'searched': searched,

        'filter_form': form,

        'title': _("Discounts"),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/discounts.html', context) 


@login_required
def add_discount(request, company):
    c = get_object_or_404(Company, url_name=company)

    # check for permission for adding discounts
    if not has_permission(request.user, c, 'discount', 'edit'):
        return no_permission_view(request, c, _("You have no permission to add discounts."))
    
    context = {
        'title': _("Add discount"),
        'site_title': g.MISC['site_title'],
        'company': c,
        'date_format_js': get_date_format(request.user, c, 'js'),
    }

    if request.method == 'POST':
        # submit data
        form = DiscountForm(data=request.POST, user=request.user, company=c)

        if form.is_valid():
            # save the new discount and redirect back to discounts
            d = Discount(
                description=form.cleaned_data.get('description'),
                code=form.cleaned_data.get('code'),
                type=form.cleaned_data.get('type'),
                amount=form.cleaned_data.get('amount'),
                start_date=form.cleaned_data.get('start_date'),
                end_date=form.cleaned_data.get('end_date'),
                enabled=form.cleaned_data.get('enabled'),
                
                created_by=request.user,
                company=c
            )
            d.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm(user=request.user, company=c)

    context['form'] = form
    context['company'] = c
    context['add'] = True
    
    return render(request, 'pos/manage/discount.html', context)


@login_required
def edit_discount(request, company, discount_id):
    # edit an existing contact
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit discounts."))
    
    context = {
        'title': _("Edit discount"),
        'site_title': g.MISC['site_title'],
        'company': c,
        'discount_id': discount_id,
        'date_format_js': get_date_format(request.user, c, 'js'),
    }
    
    discount = get_object_or_404(Discount, id=discount_id)
        
    # check if contact actually belongs to the given company
    if discount.company != c:
        raise Http404
        
    if request.method == 'POST':
        # submit data
        form = DiscountForm(data=request.POST,
                            initial=discount_to_dict(request.user, c, discount),
                            company=c, user=request.user)

        if form.is_valid():
            discount.description = form.cleaned_data.get('description')
            discount.code = form.cleaned_data.get('code')
            discount.type = form.cleaned_data.get('type')
            discount.amount = form.cleaned_data.get('amount')
            discount.start_date = form.cleaned_data.get('start_date')
            discount.end_date = form.cleaned_data.get('end_date')
            discount.enabled = form.cleaned_data.get('enabled')
            discount.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm(initial=discount_to_dict(request.user, c, discount), user=request.user, company=c)

    context['form'] = form
    
    return render(request, 'pos/manage/discount.html', context)


@login_required
def delete_discount(request, company):
    return manage_delete_object(request, company, Discount, (
        _("You have no permission to delete discounts"),
        _("Could not delete discount: ")
    ))

