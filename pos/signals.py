from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver
from models import Bill, Permission, Company, BillCompany, Register, BillRegister, Contact, BillContact, Category, \
    Product, Tax, Discount

from datetime import datetime as dtm

from common import globals as g

# Permission
@receiver(pre_save, sender=Permission)
@receiver(pre_delete, sender=Permission)
def delete_permission_cache(**kwargs):
    """ deletes cached permissions on save or delete """
    from common.functions import permission_cache_key
    from django.core.cache import cache

    ckey = permission_cache_key(kwargs['instance'].user, kwargs['instance'].company)
    cache.delete(ckey)

# Bill
# pre-save signal: set bill's serial number
@receiver(pre_save, sender=Bill)
def set_serial(instance, **kwargs):
    if instance.serial:
        return

    # set serial number after the bill has been paid;
    from config.functions import get_company_value

    # check the prefix of bills
    bill_format = get_company_value(instance.created_by, instance.company, 'pos_bill_serial_format')
    if bill_format == 's':
        prefix = ''
    elif bill_format == 'yyyy-s':
        prefix = str(instance.timestamp.year) + '-'
    elif bill_format == 'yyyy-m-s':
        prefix = str(instance.timestamp.year) + '-' + str(instance.timestamp.month+1) + '-'
    else:
        raise ValueError("Unknown bill prefix type")

    # find bills that match the prefix
    last_bill = Bill.objects.filter(company=instance.company, serial_prefix=prefix)
    if last_bill.exists():
        # use the serial from the last matching bill and add 1
        serial_number = last_bill.order_by('-serial_number')[0].serial_number + 1
    else:
        serial_number = 1

    instance.serial_number = serial_number
    instance.serial_prefix = prefix
    instance.serial = prefix + str(serial_number)


# track changes:
# company
@receiver(post_save, sender=Company)
def company_updated(instance, **kwargs):
    from common.functions import compare_objects, copy_data

    # get the last saved object from that table and see if anything has changed
    last_object = BillCompany.objects.filter(company=instance).order_by('-datetime_created')[:1]

    if len(last_object) > 0:
        last_object = last_object[0]
        if compare_objects(last_object, instance) is True:
            # there are no changes, there's nothing to be done
            return

    # something has changed, create a new copy of instance in model
    # create a new BillCompany
    bill_company = BillCompany(
        created_by=instance.created_by,
        company=instance
    )

    copy_data(instance, bill_company)
    bill_company.save()


# register
@receiver(post_save, sender=Register)
def register_updated(instance, **kwargs):  # see comments for company_updated
    from common.functions import compare_objects, copy_data

    last_object = BillRegister.objects.filter(register=instance).order_by('-datetime_updated')[:1]

    if len(last_object) > 0:
        last_object = last_object[0]
        if compare_objects(last_object, instance) is True:
            return

    bill_register = BillRegister(
        created_by=instance.created_by,
        register=instance
    )
    copy_data(instance, bill_register)
    bill_register.save()


# contact
@receiver(post_save, sender=Contact)
def contact_updated(instance, **kwargs):
    from common.functions import compare_objects, copy_data

    last_object = BillContact.objects.filter(contact=instance).order_by('-datetime_updated')[:1]

    if len(last_object) > 0:
        last_object = last_object[0]
        if compare_objects(last_object, instance) is True:
            return

    bill_contact = BillContact(
        contact=instance,
        created_by=instance.created_by
    )
    copy_data(instance, bill_contact)
    bill_contact.save()


### synchonization
def signal_change(instance, created, action, **kwargs):
    from sync.models import Sync

    if hasattr(instance, 'company'):
        company = instance.company
    elif isinstance(instance, Company):
        company = instance
    else:
        # Should not happen
        return

    sync_objects = Sync.objects.only('seq')\
        .filter(company=company).order_by('-seq')

    last_key = 0

    if len(sync_objects) > 0:
        last_key = sync_objects[0].seq

    try:
        object = Sync.objects.get(company=company, object_id=instance.id, model=instance.__class__.__name__)
        object.seq = last_key+1
        object.action = action
        object.save()
    except Sync.DoesNotExist:
        sync = Sync(company=company,
                    action=action,
                    model=instance.__class__.__name__,
                    object_id=instance.id,
                    seq=last_key+1)
        sync.save()


@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=Contact)
@receiver(post_delete, sender=Tax)
@receiver(post_delete, sender=Discount)
@receiver(post_delete, sender=Register)
def set_serial_delete(instance, **kwargs):
    signal_change(instance, False, action='delete', **kwargs)


@receiver(post_save, sender=Category)
@receiver(post_save, sender=Product)
@receiver(post_save, sender=Contact)
@receiver(post_save, sender=Tax)
@receiver(post_save, sender=Discount)
@receiver(post_save, sender=Register)
@receiver(post_save, sender=Company)
def set_serial_save(instance, created, **kwargs):
    signal_change(instance, created, action='save', **kwargs)

