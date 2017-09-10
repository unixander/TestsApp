from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, FormView

from braces.views import LoginRequiredMixin

from questions.mixins import TopicDetailMixin
from questions.models import Topic, Question
from questions.forms import AnswerQuestionForm, TopicStartForm
from users.models import UserAnswer


class TopicDetailView(TopicDetailMixin, FormView):
    """
    Show topic details and allows to start topic
    """
    form_class = TopicStartForm
    model = Topic
    queryset = Topic.objects.all()
    context_object_name = 'topic'
    template_name_suffix = '_detail'

    def get_objects(self):
        self.object = self.get_object()
        self.topic_result = self.get_topic_result(self.object)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.topic_result
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = {
                'topic': self.object.id,
                'user': self.request.user.id
            }
        return kwargs

    def form_valid(self, form):
        self.topic_result = form.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs['topic_result'] = self.topic_result
        return kwargs


class QuestionDetailView(TopicDetailMixin, FormView):
    """
    Shows question with answers.
    """
    form_class = AnswerQuestionForm
    context_object_name = 'question'
    template_name_suffix = '_detail'
    topic_url_kwarg = 'pk'
    topic = None
    number = None

    def get_queryset(self):
        if self.topic:
            return self.topic.get_active_questions()
        return Question.objects.none()

    def get_user_answer(self, question):
        if question and self.topic_result:
            return UserAnswer.objects.filter(topic_result=self.topic_result, question=question).first()
        return None

    def get_topic(self):
        pk = self.kwargs.get(self.topic_url_kwarg)
        return get_object_or_404(Topic, pk=pk)

    def get_objects(self, queryset=None):
        self.topic = self.get_topic()
        self.object = self.get_object()
        self.topic_result = self.get_topic_result(self.topic)
        self.user_answer = self.get_user_answer(self.object)

    def get_object(self):
        self.number = int(self.kwargs.get('number'))
        qs = self.get_queryset()
        if self.number > qs.count() or self.number < 1:
            raise Http404(_('Question not found'))
        return qs[self.number - 1]

    def form_valid(self, form):
        self.user_answer = form.save()
        return super().form_valid(form)

    def check_redirect(self):
        return self.user_answer is not None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['question'] = self.object
        kwargs['topic_result'] = self.topic_result
        kwargs['instance'] = self.user_answer
        return kwargs

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs['topic'] = self.topic
        kwargs['number'] = self.number
        kwargs['topic_result'] = self.topic_result
        return kwargs


class TopicListView(LoginRequiredMixin, ListView):
    queryset = Topic.objects.order_by('id')
    context_object_name = 'topics'
    paginate_by = 10

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        return kwargs
