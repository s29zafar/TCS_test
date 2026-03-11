from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .graph import get_graph
from langchain_core.messages import HumanMessage
from .models import Conversation, Message

class ChatView(APIView):
    def post(self, request):
        user_message = request.data.get("message")
        thread_id = request.data.get("thread_id", "1") # Default to 1 for simplicity
        
        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create conversation
        conversation, _ = Conversation.objects.get_or_create(id=thread_id)
        
        # Save user message
        Message.objects.create(
            conversation=conversation,
            sender='user',
            text=user_message
        )
        
        try:
            # Run the graph
            graph = get_graph()
            inputs = {"messages": [HumanMessage(content=user_message)]}
            config = {"configurable": {"thread_id": str(thread_id)}}
            
            result = graph.invoke(inputs, config=config)
            
            # Extract last message content
            response_message = result["messages"][-1].content
            
            # Save bot message
            Message.objects.create(
                conversation=conversation,
                sender='bot',
                text=response_message
            )
            
            return Response({"response": response_message, "conversation_id": conversation.id}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
