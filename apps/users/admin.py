from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import TopicResult, UserAnswer


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


class UserAnswerAdminInline(admin.TabularInline):
    model = UserAnswer
    extra = 0


class TopicResultAdmin(admin.ModelAdmin):
    inlines = [UserAnswerAdminInline]
    list_display = ('topic', 'user', 'date_finished')
    search_fields = ('topic__title', 'user__username', 'user__first_name', 'user__last_name')


class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'topic_result')


admin.site.register(get_user_model(), UserAdmin)
admin.site.register(TopicResult, TopicResultAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
