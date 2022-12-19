from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView
)
from django.views.generic.base import TemplateResponseMixin
from .models import MainDesk, Column, Card, Comment, MainDeskFavorites, MainDeskArchive, CheckList, Metki
from .forms import CommentForm


class allauthemailconfirmation(TemplateResponseMixin):
  template_name = 'desk.html'

class LockedView(LoginRequiredMixin):
    login_url = "admin:login"


class MainDeskView(LockedView, ListView):
    template_name = 'desk.html'
    model = MainDesk
    queryset = MainDesk.objects.all()
    context_object_name = 'desks'


class MainDeskCreateView(LockedView, CreateView):
    model = MainDesk
    fields = ['title', 'image']
    template_name = 'desk_form.html'
    success_url = reverse_lazy('desks')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class MainDeskUpdateView(LockedView, UpdateView):
    model = MainDesk
    fields = ['title', 'image']
    template_name = 'desk_form.html'
    success_url = reverse_lazy('desks')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class MainDeskDeleteView(LockedView, DeleteView):
    model = MainDesk
    template_name = 'desk_confirm_delete.html'
    success_url = reverse_lazy('desks')


class MainDeskDetailView(LockedView, DetailView):
    model = MainDesk
    template_name = 'column.html'

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk')
        desk = MainDesk.objects.get(id=pk, author=self.request.user)
        columns = Column.objects.filter(desk=desk)

        context = {
          'columns': columns, 'desk': desk}
        return context


class ColumnView(LockedView, ListView):
    template_name = 'column.html'
    model = Column
    queryset = MainDesk.objects.all()
    context_object_name = 'columns'


class ColumnCreateView(LockedView, CreateView):
    model = Column
    fields = ['title']
    template_name = 'column_form.html'
    queryset = Column.objects.all()
    context_object_name = 'column-add'
    success_url = reverse_lazy('columns')

    def form_valid(self, form):
        form.instance.desk = MainDesk.objects.get(pk=self.kwargs['pk'])
        return super(ColumnCreateView, self).form_valid(form)


class ColumnUpdateView(LockedView, UpdateView):
    model = Column
    fields = ['title']
    template_name = 'column_form.html'
    success_url = reverse_lazy('columns')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ColumnDeleteView(LockedView, DeleteView):
    model = Column
    template_name = 'column_confirm_delete.html'
    success_url = reverse_lazy('columns')


class ColumnDetailView(LockedView, DetailView):
    model = Column
    template_name = 'column.html'

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk')
        column = Column.objects.get(id=pk, author=self.request.user)
        cards = Card.objects.filter(column=column)

        context = {
          'cards': cards, 'column': column}
        return context


class CardView(LockedView, ListView):
    template_name = 'column.html'
    model = Card
    queryset = Column.objects.all()
    context_object_name = 'cards'


class CardCreateView(LockedView, CreateView):
    model = Card
    fields = ['title', 'content', 'deadline', 'choice', 'docfile']
    template_name = 'card_form.html'
    queryset = Card.objects.all()
    context_object_name = 'card-add'
    success_url = reverse_lazy('columns')

    def form_valid(self, form):
        form.instance.column = Column.objects.get(pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        return super(CardCreateView, self).form_valid(form)


class CardUpdateView(LockedView, UpdateView):
    model = Card
    fields = ['title', 'content', 'deadline', 'choice', 'docfile']
    template_name = 'card_form.html'
    success_url = reverse_lazy('columns')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CardDeleteView(LockedView, DeleteView):
    model = Card
    template_name = 'card_confirm_delete.html'
    success_url = reverse_lazy('columns')


class CardDetailView(LockedView, FormView, DetailView):
  template_name = "view_detail.html"
  model = Card
  context_object_name = 'entry'
  form_class = CommentForm
  success_url = "#"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['comments'] = Comment.objects.filter(entry=self.get_object()).order_by('-created_on')
    context['form'] = CommentForm()
    return context

  def post(self, request, *args, **kwargs):
    if self.request.method == 'POST':
      form = CommentForm(self.request.POST)
      if form.is_valid():
        comment = Comment(
          author=self.request.user,
          body=form.cleaned_data["body"],
          entry=self.get_object(),
        )
        comment.save()

      return super().form_valid(form)


class SearchView(ListView):
  model = MainDesk
  template_name = 'desk.html'
  context_object_name = 'desks'
  queryset = MainDesk.objects.all()

  def get_queryset(self, *args, **kwargs):
    qs = super().get_queryset(*args, **kwargs)
    query = self.request.GET.get('q')
    if query:
      return qs.filter(title__icontains=query).order_by('-created_date')
    return qs


class FavouriteListView(ListView):
    template_name = 'favourites.html'
    model = MainDeskFavorites
    queryset = MainDeskFavorites.objects.all()
    context_object_name = 'favourites'

    def get(self, *args, **kwargs):
      favourites = MainDeskFavorites.objects.filter(author=self.request.user)
      context = {
        'favourites': favourites,
      }
      return render(self.request, 'favourites.html', context)


def favorites_list(request):
  context = {}
  return render(request, 'favorites.html', context=context)


def add_to_favorites(request, id):
  if request.method == 'POST':
    if not request.session.get('favorites'):
      request.session['favorites'] = list()
    else:
      request.session['favorites'] = list(request.session['favorites'])

    item_exist = next((item for item in request.session['favorites'] if item['type'] == request.POST.get('type') and item['id'] == id), False)

    add_data = {
      'type': request.POST.get('type'),
      'id': id,
    }

    if not item_exist:
      request.session['favorites'].append(add_data)
      request.session.modified = True
  return redirect(request.POST.get('url_from'))


def remove_from_favorites(request, id):
  if request.method == 'POST':

    for item in request.session['favorites']:
      if item['id'] == id and item['type'] == request.POST.get('type'):
        item.clear()

    while {} in request.session['favorites']:
      request.session['favorites'].remove({})

    if not request.session['favorites']:
      del request.session['favorites']

    request.session.modified = True
  return redirect(request.POST.get('url_from'))


def delete_favorites(request):
  if request.session.get('favorites'):
    del request.session['favorites']
  return redirect(request.POST.get('url_from'))


class ArchiveListView(ListView):
    template_name = 'archives.html'
    model = MainDeskArchive
    queryset = MainDeskArchive.objects.all()
    context_object_name = 'archives'

    def get(self, *args, **kwargs):
      archives = MainDeskArchive.objects.filter(author=self.request.user)
      context = {
        'archives': archives,
      }
      return render(self.request, 'archives.html', context)


def archives_list(request):
  context = {}
  return render(request, 'archives.html', context=context)


def add_to_archives(request, id):
  if request.method == 'POST':
    if not request.session.get('archives'):
      request.session['archives'] = list()
    else:
      request.session['archives'] = list(request.session['archives'])

    item_exist = next((item for item in request.session['archives'] if item['type'] == request.POST.get('type') and item['id'] == id), False)

    add_data = {
      'type': request.POST.get('type'),
      'id': id,
    }

    if not item_exist:
      request.session['archives'].append(add_data)
      request.session.modified = True
  return redirect(request.POST.get('url_from'))


def remove_from_archives(request, id):
  if request.method == 'POST':

    for item in request.session['archives']:
      if item['id'] == id and item['type'] == request.POST.get('type'):
        item.clear()

    while {} in request.session['archives']:
      request.session['archives'].remove({})

    if not request.session['archives']:
      del request.session['archives']

    request.session.modified = True
  return redirect(request.POST.get('url_from'))


def delete_archives(request):
  if request.session.get('archives'):
    del request.session['archives']
  return redirect(request.POST.get('url_from'))


class CheckListView(LockedView, ListView):
  template_name = 'view_detail.html'
  model = CheckList
  queryset = Card.objects.all()
  context_object_name = 'checklists'


class CheckListCreateView(LockedView, CreateView):
  model = CheckList
  fields = ['title', 'card', 'done']
  template_name = 'card_form.html'
  queryset = CheckList.objects.all()
  context_object_name = 'checklist-add'
  success_url = reverse_lazy('columns')

  def form_valid(self, form):
    form.instance.card = Card.objects.get(pk=self.kwargs['pk'])
    form.instance.author = self.request.user
    return super(CheckListCreateView, self).form_valid(form)


class CheckListUpdateView(LockedView, UpdateView):
  model = CheckList
  fields = ['title', 'done']
  template_name = 'card_form.html'
  success_url = reverse_lazy('columns')

  def form_valid(self, form):
    form.instance.author = self.request.user
    return super().form_valid(form)


class CheckListDeleteView(LockedView, DeleteView):
  model = CheckList
  template_name = 'checklist_confirm_delete.html'
  success_url = reverse_lazy('columns')


class MetkiView(LockedView, ListView):
  template_name = 'view_detail.html'
  model = Metki
  queryset = Card.objects.all()
  context_object_name = 'metkis'


class MetkiCreateView(LockedView, CreateView):
  model = Metki
  fields = ['title', 'card', 'colour']
  template_name = 'card_form.html'
  queryset = Metki.objects.all()
  context_object_name = 'metki-add'
  success_url = reverse_lazy('columns')

  def form_valid(self, form):
    form.instance.card = Card.objects.get(pk=self.kwargs['pk'])
    form.instance.author = self.request.user
    return super(MetkiCreateView, self).form_valid(form)


class MetkiUpdateView(LockedView, UpdateView):
  model = Metki
  fields = ['title', 'colour']
  template_name = 'card_form.html'
  success_url = reverse_lazy('columns')

  def form_valid(self, form):
    form.instance.author = self.request.user
    return super().form_valid(form)


class MetkiDeleteView(LockedView, DeleteView):
  model = Metki
  template_name = 'metki_confirm_delete.html'
  success_url = reverse_lazy('columns')