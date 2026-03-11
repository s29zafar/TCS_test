from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Conversation, Message

class ChatbotTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chat_url = reverse('chat')

    def test_models_creation(self):
        """Test that models can be created correctly."""
        conv = Conversation.objects.create()
        msg = Message.objects.create(
            conversation=conv,
            sender='user',
            text='Hello unit test'
        )
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(msg.text, 'Hello unit test')

    def test_chat_view_saves_messages(self):
        """Test that the ChatView saves messages to the database."""
        # Note: This might take time depending on the LLM/graph execution
        payload = {'message': 'Hi there', 'thread_id': 1}
        response = self.client.post(self.chat_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('response' in response.data)
        
        # Verify database state
        self.assertEqual(Conversation.objects.count(), 1)
        # Should have 2 messages: 1 user, 1 bot
        self.assertEqual(Message.objects.count(), 2)
        
        user_msg = Message.objects.get(sender='user')
        bot_msg = Message.objects.get(sender='bot')
        
        self.assertEqual(user_msg.text, 'Hi there')
        self.assertEqual(bot_msg.text, response.data['response'])
