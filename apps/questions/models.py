from django.db import models
from django.db.models import F
from django.db.models.signals import post_init, post_save
from django.utils.translation import ugettext_lazy as _


class Question(models.Model):

    """
    Question model

    text - question content
    qtype - type of question (single or multiple answers are allowed)
    """

    QTYPE_RADIO = 1
    QTYPE_CHECKBOX = 2
    QTYPES = (
        (QTYPE_RADIO, _('Single Correct Answer')),
        (QTYPE_CHECKBOX, _('Multiple Correct Answers'))
    )

    text = models.TextField()
    qtype = models.IntegerField(_('Type'), choices=QTYPES, default=QTYPE_RADIO)

    def __str__(self):
        return '{}: {}'.format(self.order, self.text)

    @property
    def is_radio(self):
        """Check if question allows only single answer"""
        return self.qtype == self.QTYPE_RADIO


class Answer(models.Model):
    """
    Answer model

    question - related question
    text - answer's content
    is_correct - shows if answer is correct for this question
    """
    question = models.ForeignKey(Question, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.text


class TopicQuestionRelation(models.Model):

    """
    Question to Topic relation model

    question - linked question
    topic - linked topic
    order - specifies order of question in topic questions list
    active - indicates if question sould be shown in topic questions list
    """

    question = models.ForeignKey(Question, related_name='topic_relation')
    topic = models.ForeignKey('questions.Topic', related_name='question_relation')
    order = models.PositiveIntegerField(default=0, blank=True)
    active = models.BooleanField(default=True, blank=True)

    class Meta:
        unique_together = ('question', 'topic')
        ordering = ('order',)
        verbose_name = _('Linked Question')
        verbose_name_plural = _('Linked Questions')


def topic_question_post_init(sender, instance, *args, **kwargs):
    # Save original order value
    instance._orig_order = instance.order


def topic_question_post_save(sender, instance, created, *args, **kwargs):
    same_order_exists = TopicQuestionRelation.objects.filter(
        topic_id=instance.topic_id,
        order=instance.order
    ).exclude(id=instance.id).exists()

    # If question with the same order exists in this topic then increase values
    # of questions with the order greater then the currect one
    if (created or instance._orig_order != instance.order) and same_order_exists:
        TopicQuestionRelation.objects.filter(
            topic_id=instance.topic_id,
            order__gte=instance.order
        ).exclude(id=instance.id).update(order=F('order') + 1)
    # Reset original value of order
    instance._orig_order = instance.order


post_init.connect(topic_question_post_init, sender=TopicQuestionRelation)
post_save.connect(topic_question_post_save, sender=TopicQuestionRelation)


class Topic(models.Model):
    """
    Topic model

    title - title of topic
    description - description of topic
    questions - questions list, related to topic
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    questions = models.ManyToManyField(Question, through=TopicQuestionRelation, related_name='topics')

    def __str__(self):
        return self.title

    def get_active_questions(self):
        """Get active questions of topic"""
        return self.questions.filter(
            topic_relation__active=True
        ).order_by('topic_relation', 'id')
