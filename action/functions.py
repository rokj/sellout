
# for json etc.
import json
from pos.views.manage.company import company_to_dict


def action_to_dict(user, notification, android=False):
    c = {
        'id': notification.id,
        'company': company_to_dict(user, notification.company, android, with_config=True),
        'sender': notification.sender,
        'receiver': notification.receiver,
        'type': notification.type,
        'status': notification.status,
        'data': json.loads(notification.data),
        'reference': notification.reference
        }
    return c