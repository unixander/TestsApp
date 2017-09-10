from django.conf.urls import url, include
from .views import TopicDetailView, QuestionDetailView, TopicListView


urlpatterns = [
    url(r'^$', TopicListView.as_view(), name='topic-list'),
    url(r'^(?P<pk>\d+)/', include([
        url('^$', TopicDetailView.as_view(), name='topic-detail'),
        url(r'^question-(?P<number>\d+)/$', QuestionDetailView.as_view(), name='question-detail')
    ]))
]
