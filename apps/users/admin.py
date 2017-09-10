from django.contrib import admin

from users.models import TopicResult, UserAnswer


class UserAnswerAdminInline(admin.TabularInline):
    model = UserAnswer
    extra = 0


class TopicResultAdmin(admin.ModelAdmin):
    inlines = [UserAnswerAdminInline]
    list_display = ('topic', 'user', 'date_finished')
    search_fields = ('topic__title', 'user__username', 'user__first_name', 'user__last_name')


class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'topic_result')


admin.site.register(TopicResult, TopicResultAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
