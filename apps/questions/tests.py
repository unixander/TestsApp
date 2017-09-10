from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.test import TestCase
from django.utils import timezone

from model_mommy import mommy

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
from questions.forms import (
    AnswerInlineFormSet,
    TopicQuestionRelationFormSet
)


class TopicListViewTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.url = reverse('topic-list')

    def test_unauthenticated_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_access(self):
        test_data = [
            ('Topic1', 'Description1'),
            ('Topic2', 'Description2'),
            ('Topic3', 'Description3'),
            ('Topic4', 'Description4'),
        ]
        for title, description in test_data:
            mommy.make(Topic, title=title, description=description)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for title, description in test_data:
            self.assertContains(response, title)


class TopicDetailViewTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.url = reverse('topic-list')

    def test_unauthenticated_access(self):
        topic = mommy.make(Topic)
        url = reverse('topic-detail', kwargs={'pk': topic.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_topic_detail_view(self):
        self.client.force_login(self.user)
        topic = mommy.make(Topic, title='Title1', description='Description1')
        url = reverse('topic-detail', kwargs={'pk': topic.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, topic.title)
        self.assertContains(response, topic.description)

    def test_start_topic(self):
        self.client.force_login(self.user)
        topic = mommy.make(Topic, title='Title1', description='Description1')
        question = mommy.make(Question, text='question1')
        answer = mommy.make(Answer, question=question, text='answer1', is_correct=True)
        mommy.make(TopicQuestionRelation, question=question, topic=topic, order=0, active=True)

        question2 = mommy.make(Question, text='question2')
        mommy.make(Answer, question=question2, text='answer1', is_correct=True)
        mommy.make(TopicQuestionRelation, question=question2, topic=topic, order=1, active=True)

        url = reverse('topic-detail', kwargs={'pk': topic.pk})
        redirect_url = reverse('question-detail', kwargs={'pk': topic.pk, 'number': 1})
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, redirect_url)
        self.assertTrue(TopicResult.objects.filter(
            topic=topic, user=self.user, date_finished__isnull=True).exists())
        self.assertContains(response, question.text)
        self.assertContains(response, answer.text)

    def test_get_finished_topic(self):
        self.client.force_login(self.user)
        topic = mommy.make(Topic, title='Title1', description='Description1')
        question = mommy.make(Question, text='question1')
        answer = mommy.make(Answer, question=question, text='answer1', is_correct=True)
        mommy.make(TopicQuestionRelation, question=question, topic=topic, order=0, active=True)
        result = mommy.make(TopicResult, topic=topic, user=self.user, date_finished=timezone.now())
        mommy.make(UserAnswer, topic_result=result, question=question, answers=[answer])

        url = reverse('topic-detail', kwargs={'pk': topic.pk})
        response = self.client.get(url)
        self.assertContains(response, 'Congratulation')
        self.assertNotContains(response, 'Go to questions')
        self.assertContains(response, '100%')


class QuestionDetailViewTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.topic = mommy.make(Topic)
        self.question1 = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)
        self.answer1 = mommy.make(Answer, question=self.question1, text='answer1', is_correct=True)
        self.relation1 = mommy.make(
            TopicQuestionRelation, question=self.question1, topic=self.topic, order=0, active=True)

        self.question2 = mommy.make(Question, text='question2', qtype=Question.QTYPE_CHECKBOX)
        self.answer2 = mommy.make(Answer, question=self.question2, text='answer1', is_correct=True)
        self.relation2 = mommy.make(
            TopicQuestionRelation, question=self.question2, topic=self.topic, order=1, active=True)

        self.question3 = mommy.make(Question, text='question3', qtype=Question.QTYPE_RADIO)
        self.answer3 = mommy.make(Answer, question=self.question3, text='answer1', is_correct=True)
        self.relation3 = mommy.make(
            TopicQuestionRelation, question=self.question3, topic=self.topic, order=2, active=True)

        self.topic_result = mommy.make(TopicResult, user=self.user, topic=self.topic, date_finished=None)

    def test_unauthenticated_access(self):
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_invalid_question_number(self):
        self.client.force_login(self.user)
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 50})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_question_answer(self):
        self.client.force_login(self.user)

        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 1})
        response = self.client.post(url, data={'answer': self.answer1.id}, folow=True)

        url2 = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 2})
        self.assertRedirects(response, url2)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question1,
            answers__id=self.answer1.id
        ).exists())

        response = self.client.post(url, data={'answer': self.answer1.id}, folow=True)
        self.assertRedirects(response, url2)
        self.assertEquals(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question1,
            answers__id=self.answer1.id
        ).count(), 1)

    def test_question_no_answer(self):
        self.client.force_login(self.user)

        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 1})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'At least one answer should be selected')

    def test_question_multiple_answers(self):
        self.client.force_login(self.user)

        answer2 = mommy.make(Answer, question=self.question2, text='answer2', is_correct=True)
        answer3 = mommy.make(Answer, question=self.question2, text='answer3')

        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 2})
        response = self.client.post(url, data={
            'answer_{}'.format(self.answer2.id): True,
            'answer_{}'.format(answer2.id): True
        }, folow=True)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question2,
            answers__id=self.answer2.id
        ).exists())

        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question2,
            answers__id=answer2.id
        ).exists())

        self.assertFalse(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question2,
            answers__id=answer3.id
        ).exists())

    def test_questions_sequence(self):
        self.client.force_login(self.user)

        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 1})
        response = self.client.post(url, data={'answer': self.answer1.id}, folow=True)

        # First question
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 2})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question1,
            answers__id=self.answer1.id
        ).exists())

        # Second question
        response = self.client.post(url, data={'answer_{}'.format(self.answer2.id): True}, folow=True)
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 3})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question2,
            answers__id=self.answer2.id
        ))

        # Third question
        response = self.client.post(url, data={'answer': self.answer3.id}, folow=True)

        url = reverse('topic-detail', kwargs={'pk': self.topic.pk})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question3,
            answers__id=self.answer3.id
        ).exists())

        self.assertTrue(TopicResult.objects.filter(
            id=self.topic_result.id, date_finished__isnull=False).exists())

    def test_questions_sequence_changed(self):
        self.client.force_login(self.user)

        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 1})
        response = self.client.post(url, data={'answer': self.answer1.id}, folow=True)

        # First question
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 2})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question1,
            answers__id=self.answer1.id
        ).exists())

        # Second question
        response = self.client.post(url, data={'answer_{}'.format(self.answer2.id): True}, folow=True)
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 3})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question2,
            answers__id=self.answer2.id
        ))

        # Added new question while user was not on website

        new_question = mommy.make(Question, text='question4', qtype=Question.QTYPE_RADIO)
        new_answer = mommy.make(Answer, question=new_question, text='answer4', is_correct=True)
        mommy.make(
            TopicQuestionRelation, question=new_question, topic=self.topic, order=2, active=True)

        self.relation3.order = 3
        self.relation3.save()

        url = reverse('topic-detail', kwargs={'pk': self.topic.pk})
        response = self.client.post(url, follow=True)

        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 3})
        self.assertRedirects(response, url)
        self.assertContains(response, new_question.text)
        self.assertContains(response, new_answer.text)

        response = self.client.post(url, data={'answer': new_answer.id}, folow=True)
        url = reverse('question-detail', kwargs={'pk': self.topic.pk, 'number': 4})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=new_question,
            answers__id=new_answer.id
        ))

        # Last question
        response = self.client.post(url, data={'answer': self.answer3.id}, folow=True)

        url = reverse('topic-detail', kwargs={'pk': self.topic.pk})
        self.assertRedirects(response, url)
        self.assertTrue(UserAnswer.objects.filter(
            topic_result=self.topic_result,
            question=self.question3,
            answers__id=self.answer3.id
        ).exists())

        self.assertTrue(TopicResult.objects.filter(
            id=self.topic_result.id, date_finished__isnull=False).exists())


class QuestionModelsTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.topic = mommy.make(Topic)
        self.question1 = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)
        self.answer1 = mommy.make(Answer, question=self.question1, text='answer1', is_correct=True)
        self.relation1 = mommy.make(
            TopicQuestionRelation, question=self.question1, topic=self.topic, order=0, active=True)

        self.question2 = mommy.make(Question, text='question2', qtype=Question.QTYPE_CHECKBOX)
        self.answer2 = mommy.make(Answer, question=self.question2, text='answer1', is_correct=True)
        self.relation2 = mommy.make(
            TopicQuestionRelation, question=self.question2, topic=self.topic, order=1, active=True)

        self.question3 = mommy.make(Question, text='question3', qtype=Question.QTYPE_RADIO)
        self.answer3 = mommy.make(Answer, question=self.question3, text='answer1', is_correct=True)
        self.relation3 = mommy.make(
            TopicQuestionRelation, question=self.question3, topic=self.topic, order=2, active=True)

        self.topic_result = mommy.make(TopicResult, user=self.user, topic=self.topic, date_finished=None)

    def test_order_change(self):
        question = mommy.make(Question, text='question2', qtype=Question.QTYPE_CHECKBOX)
        mommy.make(
            TopicQuestionRelation, question=question, topic=self.topic, order=1, active=True)

        self.assertTrue(TopicQuestionRelation.objects.filter(id=self.relation2.id, order=2).exists())
        self.assertTrue(TopicQuestionRelation.objects.filter(id=self.relation3.id, order=3).exists())

    def test_get_active_questions(self):
        self.assertEqual(self.topic.get_active_questions().count(), 3)

        self.relation3.active = False
        self.relation3.save()

        self.assertEqual(self.topic.get_active_questions().count(), 2)


class QuestionAdminFormsetTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.topic = mommy.make(Topic)
        self.question = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)
        self.answer1 = mommy.make(Answer, question=self.question, text='answer1', is_correct=True)
        self.answer2 = mommy.make(Answer, question=self.question, text='answer1', is_correct=True)
        self.answer3 = mommy.make(Answer, question=self.question, text='answer1', is_correct=False)
        self.relation = mommy.make(
            TopicQuestionRelation, question=self.question, topic=self.topic, order=0, active=True)

    def test_single_answer_question(self):
        AnswerFormset = inlineformset_factory(
            Question, Answer, formset=AnswerInlineFormSet, fields=['id', 'question', 'is_correct', 'text'])
        data = {
            'answers-INITIAL_FORMS': 0,
            'answers-MAX_NUM_FORMS': 10,
            'answers-TOTAL_FORMS': 3,
            'answers-0-id': self.answer1.id,
            'answers-0-question': self.question.id,
            'answers-0-is_correct': False,
            'answers-0-text': self.answer1.text,
            'answers-1-id': self.answer2.id,
            'answers-1-question': self.question.id,
            'answers-1-is_correct': False,
            'answers-1-text': self.answer2.text,
            'answers-2-id': self.answer3.id,
            'answers-2-question': self.question.id,
            'answers-2-is_correct': False,
            'answers-2-text': self.answer3.text,
        }
        # At least one answer is required
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertFalse(answer_formset.is_valid())

        # One answer is selected - OK
        data['answers-1-is_correct'] = True
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertTrue(answer_formset.is_valid())

        # Multiple answers are selected - Error
        data['answers-0-is_correct'] = True
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertFalse(answer_formset.is_valid())

    def test_multiple_answer_question(self):
        self.question.qtype = Question.QTYPE_CHECKBOX
        self.question.save()
        AnswerFormset = inlineformset_factory(
            Question, Answer, formset=AnswerInlineFormSet, fields=['id', 'question', 'is_correct', 'text'])
        data = {
            'answers-INITIAL_FORMS': 0,
            'answers-MAX_NUM_FORMS': 10,
            'answers-TOTAL_FORMS': 3,
            'answers-0-id': self.answer1.id,
            'answers-0-question': self.question.id,
            'answers-0-is_correct': False,
            'answers-0-text': self.answer1.text,
            'answers-1-id': self.answer2.id,
            'answers-1-question': self.question.id,
            'answers-1-is_correct': False,
            'answers-1-text': self.answer2.text,
            'answers-2-id': self.answer3.id,
            'answers-2-question': self.question.id,
            'answers-2-is_correct': False,
            'answers-2-text': self.answer3.text,
        }
        # At least one answer is required
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertFalse(answer_formset.is_valid())

        # One answer is selected - OK
        data['answers-1-is_correct'] = True
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertTrue(answer_formset.is_valid())

        # Multiple answers are selected - OK
        data['answers-0-is_correct'] = True
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertTrue(answer_formset.is_valid())

        # All answers cannot be selected
        data['answers-2-is_correct'] = True
        answer_formset = AnswerFormset(data, instance=self.question)
        self.assertFalse(answer_formset.is_valid())


class TopicAdminFormsetTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = mommy.make(User, username='test', password='123')
        self.topic = mommy.make(Topic)
        self.question = mommy.make(Question, text='question1', qtype=Question.QTYPE_RADIO)

    def test_active_questions_selection(self):
        QuestionsFormSet = inlineformset_factory(
            Topic, TopicQuestionRelation,
            formset=TopicQuestionRelationFormSet, fields=['question', 'active', 'order', 'topic'])
        data = {
            'question_relation-INITIAL_FORMS': 0,
            'question_relation-MAX_NUM_FORMS': 10,
            'question_relation-TOTAL_FORMS': 1,
            'question_relation-0-question': self.question.id,
            'question_relation-0-active': False,
            'question_relation-0-order': 0,
            'question_relation-0-topic': self.topic.id,
        }
        # No active questions
        questions_formset = QuestionsFormSet(data, instance=self.topic)
        self.assertFalse(questions_formset.is_valid())

        # One active question - OK
        data['question_relation-0-active'] = True
        questions_formset = QuestionsFormSet(data, instance=self.topic)
        self.assertTrue(questions_formset.is_valid())
