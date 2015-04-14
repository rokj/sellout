from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from common.functions import JsonParse
from django.contrib.auth.decorators import login_required as login_required_nolocking

from models import Question, Comment, Vote, Faq
from support.forms import QuestionForm, CommentForm, SearchForm

import parameters as p
import common.globals as g


#
# views
#
# login is not required for support index, but it is required for posting
def index(request, category=None):
    category_name = None

    if category:
        print 'category'
        # a category is selected, show its questions
        cats = {k[0]: k[1] for k in p.CATEGORIES}
        if category not in cats:
            raise Http404
        else:
            category_name = cats[category]

        # paginate entries in this category

        cat_questions = Question.objects.filter(category=category).order_by('-timestamp')
        paginator = Paginator(cat_questions, p.RESULTS_PER_PAGE)

        page = request.GET.get('page')
        try:
            questions = paginator.page(page)
        except PageNotAnInteger:  # first page if invalid value
            questions = paginator.page(1)
        except EmptyPage:  # last page if request is beyond all limits
            questions = paginator.page(paginator.num_pages)

        latest = None
    else:
        # there's no category selected, show latest questions from each category
        questions = None
        latest = []
        for c in p.CATEGORIES:
            latest.append({
                'category_id': c[0],
                'category_name': c[1],
                'questions': Question.objects.filter(category=c[0]).order_by('-timestamp')[:p.LATEST_COUNT]
            })

    c = {
        'categories': p.CATEGORIES,
        'category': category,
        'category_name': category_name,

        'questions': questions,
        'latest': latest,

        'search_form': SearchForm(),

        'title': _("Support"),
        'site_title': g.SITE_TITLE,
    }

    return render(request, 'support/index.html', c)


# @login_not_required
def search(request):
    # preserve GET parameters from search (if any)
    # 'queries' will be added to pagination links in template
    # Kudos: https://djangosnippets.org/snippets/1592/
    prev_get = request.GET.copy()
    if 'page' in prev_get:
        del prev_get['page']

    # in case nothing was searched for
    results = Comment.objects.none()

    # the 'search' form
    if request.method == 'GET':
        form = SearchForm(request.GET)
        if form.is_valid():
            # search and return search results
            category = form.cleaned_data.get('category')

            query = Q()

            for w in form.cleaned_data.get('search_text').split():
                # search comments and their questions
                query = query | Q(text__icontains=w) | \
                    Q(question__title__icontains=w) | Q(question__text__icontains=w)

            results = Comment.objects.filter(query).distinct('question').order_by('question')

            if category != '-':
                results = results.filter(question__category=category)
    else:
        # (an empty search form, this should never happen:
        #  user should always visit this url from a form in another view)
        form = SearchForm()

    # paginate results
    paginator = Paginator(results, p.RESULTS_PER_PAGE)
    page = request.GET.get('page')
    try:
        paged_results = paginator.page(page)
    except PageNotAnInteger:  # first page if invalid value
        paged_results = paginator.page(1)
    except EmptyPage:  # last page if request is beyond all limits
        paged_results = paginator.page(paginator.num_pages)

    c = {
        'results': paged_results,
        'prev_get': prev_get,

        'search_form': form,
        'categories': p.CATEGORIES,
        'title': _("Support"),
        'site_title': g.SITE_TITLE,
    }

    return render(request, 'support/search_results.html', c)


def faq(request):
    # return all FAQ answers , ordered by category
    # structure of faqs:
    # [
    #  category1: [faq1, faq2, faq3]
    #  category2: [faq1, faq2, faq3]
    # ]
    faqs = []

    for i in p.CATEGORIES:
        faqs.append({
            'category_code': i[0],
            'category_name': i[1],
            'faqs': Faq.objects.filter(category=i[0]),
        })

    context = {
        'categories': faqs,
        'search_form': SearchForm(),

        'title': _("Frequently Asked Questions"),
        'site_title': g.SITE_TITLE,
    }

    return render(request, 'support/faq.html', context)


# @login_not_required
def question(request, question_id):
    # show the question and comment form (if user is logged in)
    try:
        q = Question.objects.get(id=question_id)
    except (Question.DoesNotExist, ValueError):
        raise Http404

    # get all comments
    a = Comment.objects.filter(question=q)

    # permissions
    logged_in = request.user.is_authenticated()

    # the 'comment' form
    if request.method == 'POST' and logged_in:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = Comment(
                created_by=request.user,
                author=request.user,
                question=q,  # for this question, obviously
                text=comment_form.cleaned_data['text'],
                is_answer=False
            )
            comment.save()

            return redirect(reverse('support:question', args=(question_id,)))
    else:
        comment_form = CommentForm()

    c = {
        'categories': p.CATEGORIES,
        'search_form': SearchForm(),
        'question': q,
        'comments': a,
        'can_add': logged_in,
        'can_delete': q.can_delete(request.user),
        'comment_form': comment_form,
        'current_user': request.user,
        'logged_in': logged_in,

        'title': q.title,
        'site_title': g.SITE_TITLE,
    }

    return render(request, 'support/question.html', c)


@login_required_nolocking
def ask(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            q = Question(
                created_by=request.user,
                author=request.user,
                category=form.cleaned_data['category'],
                title=form.cleaned_data['title'],
                text=form.cleaned_data['text'],
            )
            q.save()

            return redirect(reverse('support:question', args=(q.id,)))
    else:
        form = QuestionForm()

    c = {
        'form': form,
        'search_form': SearchForm(),

        'categories': p.CATEGORIES,

        'title': _("Ask a question"),
        'site_title': g.SITE_TITLE,
    }

    return render(request, 'support/ask.html', c)


@login_required_nolocking
def vote(request):
    # there's 'question_id' and 'up' in request.POST;
    # before doing anything, check if this user already voted on that question
    d = JsonParse(request.POST.get('data'))

    try:
        question_id = int(d.get('question_id'))
        v = int(d.get('up'))
    except:
        return JsonResponse({'status': 'error', 'message': _("Not enough data")})

    # get the question
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _("Question does not exist")})

    # check if user has voted already
    if Vote.objects.filter(question=question, user=request.user).exists():
        return JsonResponse({'status': 'error', 'message': _("You already voted on this question")})

    # everything OK, add a Vote record and update Question
    Vote(user=request.user, created_by=request.user, question=question).save()

    if v:
        question.plus += 1
    else:
        question.minus += 1

    question.save()

    return JsonResponse({'status': 'ok'})


@login_required_nolocking
def accept(request):
    # receive (comment) id in request.POST and mark that comment as an answer
    d = JsonParse(request.POST.get('data'))

    try:
        comment_id = d.get('id')
    except:
        return JsonResponse({'status': 'error', 'message': _("No comment specified")})

    # get the comment
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': _("Comment does not exist")})

    # check if an accepted answer exists already
    if Comment.objects.filter(question__id=comment.question.id, is_answer=True).exists():
        return JsonResponse({'status': 'error', 'message': _("This question already has an answer")})

    # everything OK, mark this comment as answer
    comment.is_answer = True
    comment.save()

    return JsonResponse({'status': 'ok'})


@login_required_nolocking
def delete_question(request):
    # there must be (question) id in request.POST.data
    try:
        id = int(JsonParse(request.POST.get('data')).get('id'))
        question = Question.objects.get(id=id)
    except:
        return JsonResponse({'status': 'error', 'message': _("Question not found")})

    # see if the user has permission to delete this question
    if not question.can_delete(request.user):
        return JsonResponse({'status': 'error', 'message': _("You cannot delete this question")})

    # ok, delete it.
    question.delete()
    return JsonResponse({'status': 'ok', 'url': reverse('support:index')})


@login_required_nolocking
def delete_comment(request):
    # read comment_id from request.POST.data
    try:
        id = int(JsonParse(request.POST.get('data')).get('id'))
        comment = Comment.objects.get(id=id)
    except:
        return JsonResponse({'status': 'error', 'message': _("Comment not found")})

    # check for permissions
    if not comment.can_delete(request.user):
        return JsonResponse({'status': 'error', 'message': _("You cannot delete this comment")})

    # ok, delete it and return the user back to question

    url = reverse('support:question', args=(comment.question.id,))
    comment.delete()
    return JsonResponse({'status': 'ok', 'url': url})