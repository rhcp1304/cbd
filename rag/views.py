from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .helpers import rag_helper


@csrf_exempt
def natural_language_query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '').strip()

            if not user_query:
                return JsonResponse({'error': 'Query cannot be empty.'}, status=400)

            # 1. Retrieve relevant data based on the user's query
            relevant_chunks = rag_helper.retrieve_relevant_data(user_query, k=5)  # Retrieve top 5 relevant chunks

            if not relevant_chunks:
                # If no relevant data is found, try to answer directly or inform the user
                context = "No specific relevant data found in the database."
                print("No relevant chunks found for query.")  # Log to console
            else:
                # Combine relevant chunks into a context string for the LLM
                context = "\n".join(relevant_chunks)
                print(f"Retrieved context:\n{context[:500]}...")  # Log first 500 chars of context

            # 2. Construct the prompt for the LLM
            # Instruct the LLM to use the provided context to answer the question.
            # Emphasize not to hallucinate.
            llm_prompt = (
                f"You are an AI assistant that answers questions based on provided context about business data. "
                f"If the answer is not in the context, state that you don't have enough information.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {user_query}\n\n"
                f"Answer:"
            )

            # 3. Get response from LLM
            llm_response = rag_helper.get_gemini_response(llm_prompt)

            return JsonResponse({'query': user_query, 'answer': llm_response})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected server error occurred: {e}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are supported.'}, status=405)