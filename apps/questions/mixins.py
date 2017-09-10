from django.shortcuts import redirect
from braces.views import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin

from users.models import TopicResult


class TopicDetailMixin(LoginRequiredMixin,
                       SingleObjectTemplateResponseMixin,
                       SingleObjectMixin):

    """
    Mixin for subviews with Topic as parent object.
    """

    topic_results = None

    def get(self, request, *args, **kwargs):
        self.get_objects()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_objects()
        if self.check_redirect():
            return redirect(self.get_success_url())
        return super().post(request, *args, **kwargs)

    def get_topic_result(self, topic):
        """ Get user's topic results by topic"""
        if topic:
            return TopicResult.objects.filter(topic_id=topic.id, user=self.request.user).first()
        return None

    def check_redirect(self):
        return self.topic_result is not None

    def get_success_url(self):
        next_number = self.topic_result.get_next_number(allow_finish=True)
        if next_number:
            return reverse('question-detail', kwargs={
                'pk': self.topic_result.topic_id,
                'number': next_number
            })
        return reverse('topic-detail', kwargs={'pk': self.topic_result.topic_id})
