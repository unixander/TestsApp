from django.contrib import admin

from questions.models import Answer, Question, Topic, TopicQuestionRelation
from questions.forms import AnswerInlineFormSet, TopicQuestionRelationFormSet


class AnswerAdminInline(admin.TabularInline):
    model = Answer
    formset = AnswerInlineFormSet
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    inlines = [
        AnswerAdminInline,
    ]
    list_display = ('text', 'qtype')
    search_fields = ('text',)
    list_filter = ('qtype',)


class TopicQuestionRelationAdminInline(admin.TabularInline):
    model = TopicQuestionRelation
    formset = TopicQuestionRelationFormSet
    extra = 1


class TopicAdmin(admin.ModelAdmin):
    inlines = [
        TopicQuestionRelationAdminInline,
    ]
    list_display = ('title', 'description')
    search_fields = ('title', 'description')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Topic, TopicAdmin)
