from django.core.management.base import BaseCommand, CommandError
from ...helpers import rag_helper as helper

class Command(BaseCommand):
    help = 'Queries the RAG system with natural language and retrieves a Gemini response.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query_text',
            nargs='?',
            type=str,
            help='The natural language query to ask the RAG system.'
        )
        parser.add_argument(
            '--build-index',
            action='store_true',
            help='Force rebuild the FAISS index before querying.'
        )
        parser.add_argument(
            '--k',
            type=int,
            default=500,
            help='Number of top relevant chunks to retrieve from FAISS. Default is 100.'
        )

    def handle(self, *args, **options):
        query_text = options['query_text']
        build_index_flag = options['build_index']
        k_chunks = options['k']
        log_func = self.stdout.write

        if build_index_flag:
            log_func(self.style.NOTICE("Attempting to rebuild FAISS index..."))
            if not helper.build_and_save_faiss_index(logger=log_func):
                raise CommandError("Failed to build FAISS index. Check logs for details.")
            log_func(self.style.SUCCESS("FAISS index rebuilt successfully."))

        faiss_index, original_texts = helper.load_faiss_index_and_texts(logger=log_func)

        if faiss_index is None or original_texts is None:
            raise CommandError(
                self.style.ERROR(
                    "FAISS index or text mapping not found. "
                    "Please run 'python manage.py rag_query --build-index' first "
                    "to build the index from your GoogleSheetData."
                )
            )

        if not query_text:
            raise CommandError("Please provide a query text. Example: python manage.py rag_query \"What are the sales figures for Q1?\"")

        log_func(self.style.SUCCESS(f"Querying for: '{query_text}'"))

        log_func(self.style.NOTICE("Retrieving relevant data chunks..."))
        relevant_chunks = helper.retrieve_relevant_data(query_text, k=k_chunks, logger=log_func)

        if not relevant_chunks:
            log_func(self.style.WARNING("No relevant data chunks found for your query. Sending query to LLM without specific context."))
            context_for_llm = "No specific context found from your data."
        else:
            log_func(self.style.SUCCESS(f"Found {len(relevant_chunks)} relevant chunks."))
            context_for_llm = "\n\n".join(relevant_chunks)

        prompt_for_gemini = (
            "You are a helpful assistant that answers questions based on the provided context. "
            "If the answer is not available in the context, state that you don't have enough information.\n\n"
            f"Context:\n{context_for_llm}\n\n"
            f"Question: {query_text}\n\n"
            "Answer:"
        )

        # Step 3: Get response from Gemini
        log_func(self.style.NOTICE("Sending prompt to Gemini for final answer..."))
        gemini_response = helper.get_gemini_response(prompt_for_gemini, logger=log_func)

        log_func(self.style.HTTP_INFO("\n--- Gemini's Response ---"))
        log_func(gemini_response)
        log_func(self.style.HTTP_INFO("-------------------------\n"))