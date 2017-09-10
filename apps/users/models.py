from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, Case, When, F
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel

from questions.models import Topic, Answer, Question


class User(AbstractUser):
    """
    User overrided model, additional fields can be added here
    """

    class Meta(AbstractUser.Meta):
        pass

    def __str__(self):
        return self.username


class TopicResult(TimeStampedModel):

    topic = models.ForeignKey(Topic, related_name='results')
    user = models.ForeignKey(get_user_model(), related_name='results')
    result = models.PositiveIntegerField(blank=True, default=0)
    date_finished = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('User\'s Topic Result')
        verbose_name_plural = _('User\'s Topic Results')

    def __str__(self):
        return '{0} - {1}'.format(self.user, self.topic)

    def get_active_answers(self, with_correct_fields=False):
        answers = self.answers.select_related('question').filter(
            question__topic_relation__active=True,
            question__topic_relation__topic_id=self.topic_id
        )

        if with_correct_fields:
            answers = answers.prefetch_related('answers').annotate(
                correct_count=Sum(
                    Case(
                        When(answers__is_correct=True, then=1),
                        default=0, output_field=models.IntegerField()
                    )
                ),
                total_correct=RawSQL(
                    """
                    SELECT count(*)
                        FROM "questions_answer"
                        WHERE question_id="users_useranswer".question_id AND is_correct=True
                    """,
                    params=(),
                    output_field=models.IntegerField()
                )
            )
        return answers

    @property
    def answered_count(self):
        """
        Total answered questions count
        """
        self.__answered_count = getattr(self, '__answered_count', None)
        if self.__answered_count is None:
            self.__answered_count = self.get_active_answers().count()
        return self.__answered_count

    @property
    def correct_count(self):
        """Correct answered questions count"""
        self.__incorrect_count = getattr(self, '__incorrect_count', None)
        if self.__incorrect_count is None:
            self.__incorrect_count = self.get_active_answers(
                with_correct_fields=True).filter(total_correct=F('correct_count')).count()
        return self.__incorrect_count

    @property
    def incorrect_count(self):
        """Incorrect answered questions count"""
        self.__incorrect_count = getattr(self, '__incorrect_count', None)
        if self.__incorrect_count is None:
            self.__incorrect_count = self.get_active_answers(
                with_correct_fields=True).exclude(correct_count=F('total_correct')).count()
        return self.__incorrect_count

    @property
    def total_count(self):
        """total questions count"""
        self.__total_count = getattr(self, '__total_count', None)
        if self.date_finished:
            # If topic is already finished by user then do not count new questions into result
            self.__total_count = self.get_active_answers().count()
        if self.__total_count is None:
            self.__total_count = self.topic.get_active_questions().count()
        return self.__total_count

    @property
    def correct_ratio(self):
        return self.correct_count / self.answered_count * 100

    @property
    def incorrect_ratio(self):
        return self.incorrect_count / self.answered_count * 100

    @property
    def answered_ratio(self):
        return self.answered_count / self.total_count * 100

    @property
    def current_step(self):
        answered_questions = self.get_active_answers().values_list('question_id', flat=True)
        questions = self.topic.get_active_questions().exclude(id__in=answered_questions)
        return questions.first()

    def get_next_number(self, allow_finish=False):
        """
        Gets next question number

        allow_finish - if set to true, when there is no next question currect results will be finished
        returns 0 if there is no next question and question number otherwise
        """
        questions = list(self.topic.get_active_questions().values_list('id', flat=True))
        current = self.current_step
        result = 0
        if current:
            result = questions.index(current.id) + 1
        if not result and allow_finish:
            self.date_finished = timezone.now()
            self.save()
        return result


class UserAnswer(TimeStampedModel):

    topic_result = models.ForeignKey(TopicResult, related_name='answers')
    answers = models.ManyToManyField(Answer)
    question = models.ForeignKey(Question)

    class Meta:
        unique_together = ('topic_result', 'question')

    def __str__(self):
        return 'Answer of {0} to question: {1}'.format(self.topic_result.user, self.question)
