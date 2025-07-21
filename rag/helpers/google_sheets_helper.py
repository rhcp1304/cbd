import os
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
                creds.refresh(flow.credentials)
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
                creds = flow.run_local_server(port=0)  # Opens browser for user authentication
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
        raise  # Re-raise the HttpError to be caught by the calling management command
    except Exception as e:
        log_func(f"ERROR: An unexpected error occurred while reading from Google Sheet: {e}")
        raise


def sanitize_header_oauth(header_name):
    s = re.sub(r'[^a-zA-Z0-9_]', '', header_name.replace(' ', '_'))
    s = s.strip('_')
    if not s:
        return "column_unnamed"
    if s and s[0].isdigit():
        s = '_' + s
    return s


def create_table_from_headers_oauth(cursor, table_name, headers, logger=None):
    log_func = logger if logger else print
    sanitized_headers = [sanitize_header_oauth(h) for h in headers]
    if not sanitized_headers:
        raise ValueError("No valid headers found to create table.")
    seen = {}
    unique_sanitized_headers = []
    for h in sanitized_headers:
        if h in seen:
            seen[h] += 1
            unique_sanitized_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_sanitized_headers.append(h)
    columns_sql_parts = ['"id" INTEGER PRIMARY KEY AUTOINCREMENT']
    columns_sql_parts.extend([f'"{col_name}" TEXT' for col_name in unique_sanitized_headers])
    columns_sql = ", ".join(columns_sql_parts)
    create_table_sql = f'CREATE TABLE "{table_name}" ({columns_sql})'
    log_func(f"Attempting to create table '{table_name}' with schema: {create_table_sql}")

    try:
        cursor.execute(create_table_sql)
        log_func(f"Table '{table_name}' created successfully.")
    except Exception as e:
        log_func(f"Error creating table '{table_name}': {e}")
        raise ValueError(f"Error creating table '{table_name}': {e}. "
                         f"Ensure the table doesn't already exist or use --drop-table.")


def insert_data_into_db_oauth(cursor, table_name, data, logger=None):
    log_func = logger if logger else print
    if not data or len(data) < 2:
        log_func("WARNING: No data rows after header to insert.")
        return

    original_headers = data[0]
    rows_to_insert = data[1:]
    sanitized_headers = [sanitize_header_oauth(h) for h in original_headers]
    seen = {}
    unique_sanitized_headers = []
    for h in sanitized_headers:
        if h in seen:
            seen[h] += 1
            unique_sanitized_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_sanitized_headers.append(h)
    columns_for_insert = ', '.join([f'"{h}"' for h in unique_sanitized_headers])
    placeholders = ', '.join(['%s' for _ in unique_sanitized_headers])

    insert_sql = f'INSERT INTO "{table_name}" ({columns_for_insert}) VALUES ({placeholders})'
    log_func(f"Preparing to insert {len(rows_to_insert)} rows into '{table_name}'.")
    num_expected_columns = len(unique_sanitized_headers)
    padded_rows = []
    for row in rows_to_insert:
        padded_row = list(row) + [None] * (num_expected_columns - len(row))
        padded_rows.append(padded_row[:num_expected_columns])

    try:
        cursor.executemany(insert_sql, padded_rows)
        log_func(f"Successfully inserted {len(padded_rows)} rows.")
    except Exception as e:
        log_func(f"Error inserting data into '{table_name}': {e}")
        raise ValueError(f"Error inserting data into '{table_name}': {e}")