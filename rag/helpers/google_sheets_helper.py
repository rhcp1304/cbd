import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CLIENT_SECRETS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_google_sheets_service_oauth(client_secrets_file, token_file, scopes, logger=None):
    log_func = logger if logger else print
    creds = None
    if os.path.exists(token_file):
        log_func(f"Loading credentials from {token_file}...")
        try:
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        except Exception as e:
            log_func(f"ERROR: Error loading token file: {e}. Attempting re-authentication.")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log_func("WARNING: Refreshing expired credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                log_func(f"ERROR: Error refreshing token: {e}. Re-authenticating...")
                creds = None

        if not creds:
            log_func("No valid credentials found. Initiating authentication flow (check your browser)...")
            if not os.path.exists(client_secrets_file):
                raise ValueError(
                    f"OAuth client secrets file '{client_secrets_file}' not found. "
                    "Please download it from Google Cloud Console (Desktop app type) "
                    "and place it in your project's base directory or specify with --client-secrets."
                )
            try:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
                log_func(
                    "Please open the URL displayed in your console to authenticate, if a browser doesn't open automatically."
                )
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise ValueError(f"Authentication failed: {e}")
        log_func(f"Saving new credentials to {token_file}...")
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            log_func(f"ERROR: Could not save token.json: {e}. Check file permissions.")

    log_func("Authentication successful.")
    return build('sheets', 'v4', credentials=creds)


def read_data_from_sheet_oauth(service, spreadsheet_id, range_name, logger=None):
    log_func = logger if logger else print
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        if not values:
            log_func(f"WARNING: No data found in '{range_name}' of spreadsheet ID '{spreadsheet_id}'.")
            return None
        log_func(f"Successfully read {len(values)} rows from Google Sheet.")
        return values
    except HttpError as err:
        log_func(f"ERROR: Google Sheets API error: {err}")
        if err.resp.status == 403:
            log_func(
                "ERROR: Permission denied. Ensure your authenticated Google account has access to the spreadsheet."
            )
        elif err.resp.status == 404:
            log_func(f"ERROR: Spreadsheet ID '{spreadsheet_id}' or range '{range_name}' not found.")
        raise
    except Exception as e:
        log_func(f"ERROR: An unexpected error occurred while reading from Google Sheet: {e}")
        raise


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
            # 1. Get the Google Sheets service
            sheets_service = get_google_sheets_service_oauth(
                CLIENT_SECRETS_FILE, TOKEN_FILE, SCOPES, logger=self.stdout.write
            )

            # 2. Read data from the sheet
            data_values = read_data_from_sheet_oauth(
                sheets_service, spreadsheet_id, sheet_range, logger=self.stdout.write
            )

            if data_values:
                # The first row is typically the header
                headers = data_values[0]
                # The rest are the data rows
                data_rows = data_values[1:]

                # Create a Pandas DataFrame
                df = pd.DataFrame(data_rows, columns=headers)

                self.stdout.write(self.style.SUCCESS("\nSuccessfully read data into Pandas DataFrame:"))
                self.stdout.write(df.head().to_markdown(index=False)) # Print the first 5 rows in markdown
                self.stdout.write(f"\nDataFrame shape: {df.shape}")
            else:
                self.stdout.write(self.style.WARNING("No data was read from the Google Sheet."))

        except ValueError as ve:
            raise CommandError(f"Configuration Error: {ve}")
        except HttpError as he:
            raise CommandError(f"Google Sheets API Error: {he}")
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")

