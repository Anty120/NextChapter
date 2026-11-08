import math
from django import forms

from assistance.contracts import LANGUAGES
from .models import UploadedMedia
from .upload_validation import inspect_file


class UploadForm(forms.ModelForm):
    file = forms.FileField(label='PDF book or MP3 song', widget=forms.ClearableFileInput(attrs={
        'accept':'.pdf,.mp3,application/pdf,audio/mpeg', 'aria-describedby':'upload-limits'}))
    language = forms.ChoiceField(choices=[('', 'Choose a language'),
        *[(name,name) for name in LANGUAGES], ('Other / unknown','Other / unknown')])
    permission = forms.BooleanField(label='I own this file or have permission to upload it.')

    class Meta:
        model = UploadedMedia
        fields = ['file','title','creator','language','description','permission']
        labels = {'creator':'Author or artist (optional)', 'description':'Description (optional)'}
        widgets = {'description':forms.Textarea(attrs={'rows':3})}

    def clean_file(self):
        upload = self.cleaned_data['file']
        self.inspected = inspect_file(upload)
        return upload


class UploadProgressForm(forms.Form):
    page = forms.IntegerField(min_value=1, required=False)
    seconds = forms.FloatField(min_value=0, max_value=7200, required=False)

    def clean_seconds(self):
        seconds = self.cleaned_data.get('seconds')
        if seconds is not None and not math.isfinite(seconds):
            raise forms.ValidationError('Enter a valid listening position.')
        return seconds


class SubmissionForm(forms.Form):
    creator = forms.CharField(max_length=180, label='Author or artist attribution')
    license_name = forms.ChoiceField(label='Permission or license', choices=[
        ('','Choose one'), ('Original work','My original work'), ('CC0','CC0'),
        ('CC BY','Creative Commons Attribution'), ('CC BY-SA','Creative Commons Attribution-ShareAlike'),
        ('Public domain','Public domain'), ('Written permission','Written permission from the rights holder'),
    ])
    source_url = forms.URLField(max_length=500, required=False, label='Public source or license link (optional)',
        help_text='Shown publicly after approval. Put private permission details in the note below.')
    rights_note = forms.CharField(max_length=1500, label='Permission details',
        help_text='Explain who created this work and why you may share the entire file publicly.',
        widget=forms.Textarea(attrs={'rows':4}))
    permission = forms.BooleanField(label='I have permission to publish this file for everyone to read or listen to.')


class ReviewForm(forms.ModelForm):
    review_status = forms.ChoiceField(choices=[('pending','Awaiting review'),('approved','Published'),('rejected','Changes requested')])
    class Meta:
        model = UploadedMedia
        fields = ['review_status','review_notes']

    def clean(self):
        data = super().clean()
        if data.get('review_status') not in {'pending','approved','rejected'}:
            raise forms.ValidationError('Choose Awaiting review, Published, or Changes requested.')
        if data.get('review_status') == 'rejected' and not data.get('review_notes','').strip():
            self.add_error('review_notes','Explain the requested changes for the uploader.')
        if data.get('review_status') == 'approved' and not all([
                self.instance.creator.strip(),self.instance.rights_note.strip(),
                self.instance.license_name.strip(),self.instance.submitted_at]):
            raise forms.ValidationError('Publication requires submitted attribution and permission details.')
        return data


class UploadMetadataForm(forms.ModelForm):
    language = forms.ChoiceField(choices=UploadForm.base_fields['language'].choices)

    class Meta:
        model = UploadedMedia
        fields = ['title','creator','language','description']
        labels = {'creator':'Author or artist (optional)'}
        widgets = {'description':forms.Textarea(attrs={'rows':3})}
