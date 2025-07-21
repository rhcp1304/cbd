import os
from django.core.management.base import BaseCommand, CommandError
from ...helpers.ask_gemini_helper import query_data_with_gemini_as_agent, GEMINI_MODEL_NAME, CSV_FILE_PATH

import os
os.environ.setdefault("GOOGLE_API_KEY","AIzaSyBq2_GdMf0KhowSVSb0hn4Z_8B81kBewXY")

class Command(BaseCommand):
    help = 'Queries the Gemini AI model with context from a CSV file. Usage: python manage.py query_data "Your question here"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query_text',
            type=str,
            help='The natural language query to send to the Gemini model.',
        )
        parser.add_argument(
            '--api_key',
            type=str,
            help='Your Google Gemini API key. Recommended to set as GOOGLE_API_KEY environment variable.',
            default=os.environ.get("GOOGLE_API_KEY")
        )
        parser.add_argument(
            '--model',
            type=str,
            help=f'Specify the Gemini model to use (default: {GEMINI_MODEL_NAME}).',
            default=GEMINI_MODEL_NAME
        )
        parser.add_argument(
            '--csv_path',
            type=str,
            help=f'Path to the CSV file (default: {CSV_FILE_PATH}).',
            default=CSV_FILE_PATH
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        if not api_key:
            raise CommandError(
                "Gemini API key not provided. "
                "Please set the GOOGLE_API_KEY environment variable "
                "or use the --api_key argument."
            )

        user_query = options['query_text']
        model_name = options['model']
        csv_path = options['csv_path']

        self.stdout.write(
            self.style.NOTICE(f"Sending query to Gemini model '{model_name}' with data from '{csv_path}'..."))

        try:
            gemini_response = query_data_with_gemini_as_agent(
                file_path=csv_path,
                user_query=user_query,
                model_name=model_name,
            )
            self.stdout.write(self.style.SUCCESS(f"\n--- Gemini Response ---\n{gemini_response}"))
        except (FileNotFoundError, ValueError, Exception) as e:
            raise CommandError(str(e))