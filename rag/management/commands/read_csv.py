import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from ...helpers.google_sheets_helper import get_google_sheets_service_oauth, read_data_from_sheet_oauth, HttpError, Request, Credentials, InstalledAppFlow, build # Import necessary classes for the helper functions

CLIENT_SECRETS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class Command(BaseCommand):
    help = 'Reads data from a Google Sheet and prints its head and shape.'

    def add_arguments(self, parser):
        parser.add_argument('spreadsheet_id', type=str,
                            help='The ID of the Google Spreadsheet.')
        parser.add_argument('sheet_range', type=str,
                            help='The range of the sheet to read (e.g., "Sheet1!A:Z").')

    def handle(self, *args, **options):
        spreadsheet_id = options['spreadsheet_id']
        sheet_range = options['sheet_range']

        self.stdout.write(self.style.SUCCESS(
            f"Attempting to read data from Google Sheet ID: {spreadsheet_id}, Range: {sheet_range}"
        ))

        try:
            sheets_service = get_google_sheets_service_oauth(
                CLIENT_SECRETS_FILE, TOKEN_FILE, SCOPES, logger=self.stdout.write
            )

            data_values = read_data_from_sheet_oauth(
                sheets_service, spreadsheet_id, sheet_range, logger=self.stdout.write
            )

            if data_values:
                headers = data_values[0]
                data_rows = data_values[1:]
                df = pd.DataFrame(data_rows, columns=headers)
                self.stdout.write(self.style.SUCCESS("\nSuccessfully read data into Pandas DataFrame:"))
                self.stdout.write(df.head().to_markdown(index=False))
                self.stdout.write(f"\nDataFrame shape: {df.shape}")
            else:
                self.stdout.write(self.style.WARNING("No data was read from the Google Sheet."))

        except ValueError as ve:
            raise CommandError(f"Configuration Error: {ve}")
        except HttpError as he:
            raise CommandError(f"Google Sheets API Error: {he}")
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")
