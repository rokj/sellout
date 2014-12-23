from django.utils.translation import ugettext as _

from django import forms
from models import Question, Comment

import parameters as p

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'category', 'text']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class SearchForm(forms.Form):
    select_choices = [('-', _("Choose a category"))] + list(p.CATEGORIES)

    search_text = forms.CharField(max_length=64, min_length=3, widget=forms.TextInput(attrs={'placeholder': 'Search Anything'}))
    category = forms.ChoiceField(choices=select_choices, required=False)
