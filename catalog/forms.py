from django import forms

from .models import Comment, Report


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body', 'spoiler')
        labels = {'body': 'Your comment', 'spoiler': 'Contains spoilers'}
        widgets = {'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What stood out to you? Share a thought or a cultural connection.'})}


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason',)
        labels = {'reason': 'What should a moderator review?'}
        widgets = {'reason': forms.Textarea(attrs={'rows': 3})}


class ProgressForm(forms.Form):
    paragraph = forms.IntegerField(min_value=0, required=False)
    seconds = forms.FloatField(min_value=0, max_value=86400, required=False)
