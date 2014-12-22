from django.utils.translation import ugettext as _

CATEGORIES = (
    # max length of 1st column is 16 (defined in models.py)
    # also, the keys should be slugified (no spaces & odd characters, lowercase)
    ("subscriptions", _("Subscriptions and payment")),
    ("terminal", _("Terminal")),
    ("management", _("Management")),
    ("printing", _("Bills and Printing")),
    ("bugs", _("Bugs and other issues")),
    ("android app", _("Android app")),
)

LATEST_COUNT = 10  # show this much questions in latest list
RESULTS_PER_PAGE = 15