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

    def test_supervisor_node_routing(self):
        """Directly test the supervisor routing logic."""
        from .graph import supervisor_node
        from langgraph.graph import END
        
        # Case 1: Start of conversation
        state = {"messages": [], "completed_stages": [], "current_stage": ""}
        result = supervisor_node(state)
        self.assertEqual(result.goto, "Policy Check")
        self.assertEqual(result.update["current_stage"], "Policy Check")

        # Case 2: Policy Check completed
        state = {"messages": [], "completed_stages": ["Policy Check"], "current_stage": "Policy Check"}
        result = supervisor_node(state)
        self.assertEqual(result.goto, "Customer Information Check")
        self.assertEqual(result.update["current_stage"], "Customer Information Check")

        # Case 3: All stages completed
        state = {"messages": [], "completed_stages": ["Policy Check", "Customer Information Check"], "current_stage": "Customer Information Check"}
        result = supervisor_node(state)
        self.assertEqual(result.goto, END)

    def test_graph_message_flow(self):
        """Verify the graph receives messages correctly."""
        from .graph import get_graph
        from langchain_core.messages import HumanMessage
        
        graph = get_graph()
        # We can test the graph's initial state processing
        inputs = {"messages": [HumanMessage(content="Test message")]}
        # We can't easily test the full invoke without hitting the LLM, 
        # but we can check if the graph is built correctly
        self.assertIsNotNone(graph)
        self.assertIn("Policy Check", graph.nodes)
        self.assertIn("Customer Information Check", graph.nodes)
        self.assertIn("supervisor", graph.nodes)
