import re
from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _

from questions.models import Question
from users.models import UserAnswer, TopicResult


class AnswerQuestionForm(forms.ModelForm):

    class Meta:
        model = UserAnswer
        fields = ('id',)

    def __init__(self, *args, **kwargs):
        # Get topic result and question from kwargs, they are needed for initialization of question
        self.question = kwargs.pop('question')
        self.topic_result = kwargs.pop('topic_result')
        super().__init__(*args, **kwargs)
        # Initialize checkbox based question with answers
        if self.question.qtype == Question.QTYPE_CHECKBOX:
            for answer in self.question.answers.all():
                self.fields['answer_{}'.format(answer.pk)] = forms.BooleanField(
                    label=answer.text,
                    required=False,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
        # Initialize single answer question
        if self.question.qtype == Question.QTYPE_RADIO:
            choices = ((answer.pk, answer.text) for answer in self.question.answers.all())
            self.fields['answer'] = forms.ChoiceField(
                choices=choices, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
        self.answers = []

    def clean(self):
        # Validate multiple answers for question
        if self.question.qtype == Question.QTYPE_CHECKBOX:
            for key, value in self.cleaned_data.items():
                groups = re.findall(r'answer_([0-9]{1,})', key)
                if groups and value:
                    self.answers.append(groups[0])
        # Validate single answer question
        if self.question.qtype == Question.QTYPE_RADIO and self.cleaned_data.get('answer'):
            self.answers = [self.cleaned_data.get('answer')]
        if not self.answers:
            raise forms.ValidationError(_('At least one answer should be selected'))

    def save(self, commit=False):
        useranswer = super().save(commit=False)
        useranswer.topic_result = self.topic_result
        useranswer.question = self.question
        useranswer.save()
        for answer in self.answers:
            useranswer.answers.add(answer)
        return useranswer


class TopicStartForm(forms.ModelForm):

    class Meta:
        model = TopicResult
        fields = ('topic', 'user')


class AnswerInlineFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()
        correct_count = 0
        filled_count = 0
        for form in self.forms:
            if not form.is_valid():
                return  # There are other errors
            if form.cleaned_data:
                filled_count += 1
                if form.cleaned_data.get('is_correct'):
                    correct_count += 1
            if self.instance.is_radio and correct_count > 1:
                raise forms.ValidationError(_('Only one correct answer is allowed for this question type.'))

        if not correct_count:
            raise forms.ValidationError(_('Please choose correct answer.'))

        if correct_count == filled_count:
            raise forms.ValidationError(_('All answers cannot be correct.'))


class TopicQuestionRelationFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()
        active_count = 0
        for form in self.forms:
            if not form.is_valid():
                return  # There are other errors
            if form.cleaned_data and form.cleaned_data.get('active'):
                active_count += 1
        if not active_count:
            raise forms.ValidationError(_('At least one active question is required.'))
