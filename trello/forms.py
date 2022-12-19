from django.forms import ModelForm
from django import forms
from trello.models import Column


class ColumnForm(ModelForm):
	class Meta:
		model = Column
		fields = ['title']


class CommentForm(forms.Form):
	body = forms.CharField(
		widget=forms.Textarea(
			attrs={
				"class": "form-control",
				"placeholder": "Leave a comment!"
			})
	)


#
# class MainDeskFavoritesForm(ModelForm):
#
#     class Meta:
#         model = MainDeskFavorites
#         fields = ['item']