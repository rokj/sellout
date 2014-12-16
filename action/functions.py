
# for json etc.
import json


def action_to_dict(notification, android=False):
    c = {
        'id': notification.id,
        'company': notification.company,
        'sender': notification.sender,
        'receiver': notification.receiver,
        'type': notification.type,
        'status': notification.status,
        'data': json.loads(notification.data),
        'reference': notification.reference
        }
    return c