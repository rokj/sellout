from django.utils.translation import ugettext as _

CATEGORIES = (
    # max length of 1st column is 16 (defined in models.py)
    # also, the keys should be slugified (no spaces & odd characters, lowercase)
    ("usage", _("App usage")),
    ("subscription", _("Subscription and payment")),
    ("bugs", _("Bug reports")),
    ("feature-requests", _("Feature requests")),
)

LATEST_COUNT = 10  # show this much questions in latest list
RESULTS_PER_PAGE = 15