from django.core.urlresolvers import reverse
from django.db.models import F
from django.test import TestCase
from django.utils import timezone

from model_mommy import mommy
from model_mommy.recipe import Recipe, related

from questions.models import (
    Answer,
    Question,
    TopicQuestionRelation,
    Topic
)
from users.models import (
    User,
    TopicResult,
    UserAnswer
)


class TestTopicResultModel(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.topic = mommy.make(Topic)
        self.question1 = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)
        self.answer1 = mommy.make(Answer, question=self.question1, text='answer1', is_correct=True)
        self.relation1 = mommy.make(
            TopicQuestionRelation, question=self.question1, topic=self.topic, order=0, active=True)

        self.question2 = mommy.make(Question, text='question2', qtype=Question.QTYPE_CHECKBOX)
        self.answer2 = mommy.make(Answer, question=self.question2, text='answer2', is_correct=True)
        self.answer2_1 = mommy.make(Answer, question=self.question2, text='answer2_1', is_correct=True)
        self.answer2_2 = mommy.make(Answer, question=self.question2, text='answer2_2', is_correct=False)
        self.relation2 = mommy.make(
            TopicQuestionRelation, question=self.question2, topic=self.topic, order=1, active=True)

        self.question3 = mommy.make(Question, text='question3', qtype=Question.QTYPE_RADIO)
        self.answer3 = mommy.make(Answer, question=self.question3, text='answer3', is_correct=True)
        self.answer4 = mommy.make(Answer, question=self.question3, text='answer4', is_correct=False)
        self.relation3 = mommy.make(
            TopicQuestionRelation, question=self.question3, topic=self.topic, order=2, active=True)

        self.topic_result = mommy.make(TopicResult, user=self.user, topic=self.topic, date_finished=None)

    def test_active_answers(self):
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question1, answers=(self.answer1,))
        user_answer2 = mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question2, answers=(self.answer2, self.answer2_1))
        user_answer3 = mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question3, answers=(self.answer3,))

        self.assertEqual(self.topic_result.get_active_answers().count(), 3)

        self.relation2.active = False
        self.relation2.save()

        self.assertEqual(self.topic_result.get_active_answers().count(), 2)
        self.assertFalse(self.topic_result.get_active_answers().filter(id=user_answer2.id).exists())

        self.relation2.active = True
        self.relation2.save()

        self.assertEqual(
            self.topic_result.get_active_answers(
                with_correct_fields=True).filter(correct_count=F('total_correct')).count(), 3)

        user_answer3.answers = [self.answer4]
        user_answer3.save()

        self.assertEqual(
            self.topic_result.get_active_answers(
                with_correct_fields=True).exclude(correct_count=F('total_correct')).count(), 1)

        self.assertEqual(
            self.topic_result.get_active_answers(
                with_correct_fields=True).filter(correct_count=F('total_correct')).count(), 2)

    def test_answered_count(self):
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question1, answers=(self.answer1,))
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question2, answers=(self.answer2,))
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question3, answers=(self.answer3,))

        self.assertEqual(self.topic_result.answered_count, 3)

    def test_correctness_count(self):
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question1, answers=(self.answer1,))
        user_answer2 = mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question2, answers=(self.answer2,))
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question3, answers=(self.answer3,))

        self.assertEqual(self.topic_result.correct_count, 2)
        self.assertEqual(self.topic_result.incorrect_count, 1)
        self.assertEqual(self.topic_result.total_count, 3)

        self.topic_result = TopicResult.objects.get(id=self.topic_result.id)
        user_answer2.answers.add(self.answer2_2)
        self.assertEqual(self.topic_result.correct_count, 2)
        self.assertEqual(self.topic_result.incorrect_count, 1)
        self.assertEqual(self.topic_result.total_count, 3)
        self.assertEqual(self.topic_result.answered_count, 3)

        self.topic_result = TopicResult.objects.get(id=self.topic_result.id)
        user_answer2.answers.add(self.answer2_1)
        self.assertEqual(self.topic_result.correct_count, 3)
        self.assertEqual(self.topic_result.incorrect_count, 0)
        self.assertEqual(self.topic_result.total_count, 3)
        self.assertEqual(self.topic_result.answered_count, 3)

        self.topic_result = TopicResult.objects.get(id=self.topic_result.id)
        new_question = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)
        new_answer = mommy.make(Answer, question=new_question, text='answer1', is_correct=True)
        mommy.make(
            TopicQuestionRelation, question=new_question, topic=self.topic, order=0, active=True)
        self.assertEqual(self.topic_result.total_count, 4)
        self.assertEqual(self.topic_result.answered_count, 3)

        self.topic_result = TopicResult.objects.get(id=self.topic_result.id)
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=new_question, answers=(new_answer,))
        self.assertEqual(self.topic_result.correct_count, 4)
        self.assertEqual(self.topic_result.incorrect_count, 0)
        self.assertEqual(self.topic_result.total_count, 4)
        self.assertEqual(self.topic_result.answered_count, 4)

    def test_next_number(self):
        self.assertEqual(self.topic_result.get_next_number(), 1)
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question1, answers=(self.answer1,))
        self.assertEqual(self.topic_result.get_next_number(), 2)
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question2, answers=(self.answer2,))
        self.assertEqual(self.topic_result.get_next_number(), 3)
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=self.question3, answers=(self.answer3,))

        # Added new question, that should be Question number 3
        new_question = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)
        new_answer = mommy.make(Answer, question=new_question, text='answer1', is_correct=True)
        mommy.make(
            TopicQuestionRelation, question=new_question, topic=self.topic, order=2, active=True)
        self.assertEqual(self.topic_result.get_next_number(), 3)
        mommy.make(
            UserAnswer, topic_result=self.topic_result, question=new_question, answers=(new_answer,))
        self.assertEqual(self.topic_result.get_next_number(), 0)
