import os
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.conf import settings

from ...helpers import google_sheets_helper


class Command(BaseCommand):
    help = 'Loads data from a Google Spreadsheet into a database table using OAuth 2.0 user credentials.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--spreadsheet-id',
            type=str,
            help='The ID of the Google Spreadsheet to read data from.',
            default=getattr(settings, 'DEFAULT_GOOGLE_SHEET_ID', None)
        )
        parser.add_argument(
            '--range',
            type=str,
            help='The A1 notation of the range to retrieve data from (e.g., Sheet1!A:Z).',
            default=getattr(settings, 'Sheet with Spaces!A:Z', 'Sheet1!A:Z')
        )
        parser.add_argument(
            '--table-name',
            type=str,
            help='The name of the database table to load data into.',
            default=getattr(settings, 'FY26-CBD Review Tracker', 'google_sheet_data')
        )
        parser.add_argument(
            '--client-secrets',
            type=str,
            help='Path to the client_secrets.json file for OAuth 2.0. Defaults to project base directory.',
            default=getattr(settings, 'GOOGLE_SHEETS_CLIENT_SECRETS_FILE',
                            os.path.join(settings.BASE_DIR, 'client_secrets.json'))
        )
        parser.add_argument(
            '--token-file',
            type=str,
            help='Path to the token.json file for OAuth 2.0. Defaults to project base directory. This file stores authenticated user tokens.',
            default=getattr(settings, 'GOOGLE_SHEETS_TOKEN_FILE', os.path.join(settings.BASE_DIR, 'token.json'))
        )
        parser.add_argument(
            '--drop-table',
            action='store_true',
            help='Drop the table if it exists before loading new data. USE WITH CAUTION!',
        )

    def handle(self, *args, **options):
        spreadsheet_id = options['spreadsheet_id']
        range_name = options['range']
        table_name = options['table_name']
        client_secrets_path = options['client_secrets']
        token_file_path = options['token_file']
        drop_table = options['drop_table']

        if not spreadsheet_id:
            raise CommandError("Spreadsheet ID is required. Please provide it via --spreadsheet-id or in settings.py.")

        # Determine scopes from settings, or use a default if not set
        scopes = getattr(settings, 'GOOGLE_SHEETS_SCOPES', ['https://www.googleapis.com/auth/spreadsheets.readonly'])

        self.stdout.write(self.style.NOTICE(
            f"Attempting to load data from Google Sheet ID: {spreadsheet_id}, "
            f"Range: {range_name} into table: {table_name}"
        ))

        # 1. Get Google Sheets Service (using the imported OAuth helper function)
        if not os.path.exists(client_secrets_path):
            raise CommandError(
                f"OAuth client secrets file '{client_secrets_path}' not found. "
                "Please download it from Google Cloud Console (Desktop app type) "
                "and place it in your project's base directory or specify with --client-secrets."
            )
        try:
            sheets_service = google_sheets_helper.get_google_sheets_service_oauth(
                client_secrets_path, token_file_path, scopes, logger=self.stdout.write
            )
        except Exception as e:
            raise CommandError(f"Authentication failed: {e}")

        if not sheets_service:
            # The helper function prints errors; we just exit the command.
            raise CommandError("Failed to authenticate with Google Sheets. Exiting.")

        # 2. Read Data from Google Sheet (using the imported helper function)
        try:
            sheet_data = google_sheets_helper.read_data_from_sheet_oauth(
                sheets_service, spreadsheet_id, range_name, logger=self.stdout.write
            )
        except Exception as e:
            raise CommandError(f"Error reading data from Google Sheet: {e}")

        if sheet_data is None or not sheet_data:
            raise CommandError("No data found or failed to retrieve data from Google Sheet. Exiting.")

        headers = sheet_data[0]

        # 3. Connect to Django Database and Load Data
        with transaction.atomic():  # Use a transaction for atomicity
            with connection.cursor() as cursor:
                if drop_table:
                    self.stdout.write(self.style.WARNING(f"Dropping existing table '{table_name}'..."))
                    try:
                        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                        self.stdout.write(self.style.SUCCESS(f"Table '{table_name}' dropped."))
                    except Exception as e:
                        # Log the error but don't stop if drop fails (e.g., table didn't exist)
                        self.stdout.write(
                            self.style.ERROR(f"Error dropping table '{table_name}': {e}. Continuing without drop."))

                try:
                    # Create table (using the imported helper function)
                    google_sheets_helper.create_table_from_headers_oauth(
                        cursor, table_name, headers, logger=self.stdout.write
                    )
                    # Insert data (using the imported helper function)
                    google_sheets_helper.insert_data_into_db_oauth(
                        cursor, table_name, sheet_data, logger=self.stdout.write
                    )
                except Exception as e:
                    raise CommandError(f"Database operation failed: {e}")

        self.stdout.write(self.style.SUCCESS("\nData loading process completed successfully."))