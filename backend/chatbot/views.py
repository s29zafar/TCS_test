from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .graph import graph
from langchain_core.messages import HumanMessage

class ChatView(APIView):
    def post(self, request):
        user_message = request.data.get("message")
        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Run the graph
            inputs = {"messages": [HumanMessage(content=user_message)]}
            config = {"configurable": {"thread_id": "1"}} # Basic thread ID for now
            
            result = graph.invoke(inputs, config=config)
            
            # Extract last message content
            response_message = result["messages"][-1].content
            
            return Response({"response": response_message}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
