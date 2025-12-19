"""
Google Sheets Service

Single Responsibility: Google Sheets API operations using official Google client.

This service handles all interactions with Google Sheets and Drive APIs:
- Fetch list of spreadsheets from Google Drive
- Fetch sheets within a spreadsheet
- Read row data from a sheet (with optional header mapping)
"""

from typing import List, Tuple, Dict, Any, Optional
import structlog
import requests

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = structlog.get_logger(__name__)


class GoogleSheetsService:
    """
    Service to interact with Google Sheets API using official Google client.
    
    Single Responsibility: Google Sheets/Drive API operations only.
    Does NOT handle:
    - Form field logic (handled by Form)
    - Node execution logic (handled by Node)
    """
    
    # Backend API base URL for fetching credentials
    BACKEND_URL = "http://127.0.0.1:7878/api/auth"
    
    def __init__(self, account_id: str):
        """
        Initialize with a GoogleConnectedAccount ID.
        
        Args:
            account_id: UUID of the GoogleConnectedAccount
        """
        self.account_id = account_id
        self._credentials: Optional[Credentials] = None
        self._sheets_service = None
        self._drive_service = None
    
    def _get_credentials(self) -> Credentials:
        """
        Build Google credentials from stored OAuth tokens.
        Fetches fresh token from backend API if needed.
        
        Returns:
            Credentials: Google OAuth2 credentials object
            
        Raises:
            Exception: If credentials cannot be fetched
        """
        if self._credentials and self._credentials.valid:
            return self._credentials
        
        # Fetch token data from backend API
        response = requests.get(
            f"{self.BACKEND_URL}/google/accounts/{self.account_id}/credentials/",
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(
                "Failed to get credentials",
                account_id=self.account_id,
                status_code=response.status_code
            )
            raise Exception(f"Failed to get credentials: {response.status_code}")
        
        token_data = response.json()
        
        # Build Credentials object for Google API client
        self._credentials = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', [])
        )
        
        logger.debug(
            "Credentials loaded",
            account_id=self.account_id,
            has_refresh_token=bool(token_data.get('refresh_token'))
        )
        
        return self._credentials
    
    def _get_sheets_service(self):
        """
        Get or create Google Sheets API service.
        
        Returns:
            Resource: Google Sheets API service instance
        """
        if self._sheets_service is None:
            credentials = self._get_credentials()
            self._sheets_service = build('sheets', 'v4', credentials=credentials)
        return self._sheets_service
    
    def _get_drive_service(self):
        """
        Get or create Google Drive API service.
        
        Returns:
            Resource: Google Drive API service instance
        """
        if self._drive_service is None:
            credentials = self._get_credentials()
            self._drive_service = build('drive', 'v3', credentials=credentials)
        return self._drive_service
    
    def list_spreadsheets(self) -> List[Tuple[str, str]]:
        """
        List all spreadsheets in user's Drive.
        
        Uses Drive API to find all files with spreadsheet MIME type.
        
        Returns:
            List of (spreadsheet_id, name) tuples, sorted by modification time
        """
        try:
            drive = self._get_drive_service()
            
            results = drive.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                fields="files(id, name)",
                orderBy="modifiedTime desc",
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            
            logger.info(
                "Listed spreadsheets",
                account_id=self.account_id,
                count=len(files)
            )
            
            return [(f['id'], f['name']) for f in files]
            
        except HttpError as e:
            logger.error(
                "Failed to list spreadsheets",
                account_id=self.account_id,
                error=str(e)
            )
            return []
    
    def list_sheets(self, spreadsheet_id: str) -> List[Tuple[str, str]]:
        """
        List all sheets within a spreadsheet.
        
        Args:
            spreadsheet_id: The Google Spreadsheet ID
            
        Returns:
            List of (sheet_id, sheet_title) tuples
        """
        try:
            sheets = self._get_sheets_service()
            
            spreadsheet = sheets.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="sheets.properties"
            ).execute()
            
            sheet_list = spreadsheet.get('sheets', [])
            
            logger.info(
                "Listed sheets",
                spreadsheet_id=spreadsheet_id,
                count=len(sheet_list)
            )
            
            return [
                (str(s['properties']['sheetId']), s['properties']['title'])
                for s in sheet_list
            ]
            
        except HttpError as e:
            logger.error(
                "Failed to list sheets",
                spreadsheet_id=spreadsheet_id,
                error=str(e)
            )
            return []
    
    def get_row(self, spreadsheet_id: str, sheet_name: str, row_number: int) -> Dict[str, Any]:
        """
        Get data from a specific row (values only).
        
        Args:
            spreadsheet_id: The Google Spreadsheet ID
            sheet_name: Name of the sheet tab
            row_number: Row number (1-indexed)
            
        Returns:
            Dict with row data:
            {
                "row_number": 5,
                "values": ["John", "Doe", "john@example.com"],
                "spreadsheet_id": "...",
                "sheet_name": "Sheet1"
            }
            
        Raises:
            Exception: If row cannot be fetched
        """
        try:
            sheets = self._get_sheets_service()
            
            # A1 notation for the entire row
            range_notation = f"'{sheet_name}'!{row_number}:{row_number}"
            
            result = sheets.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_notation
            ).execute()
            
            values = result.get('values', [[]])[0] if result.get('values') else []
            
            logger.info(
                "Row retrieved",
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                row_number=row_number,
                columns=len(values)
            )
            
            return {
                "row_number": row_number,
                "values": values,
                "range": result.get('range'),
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name
            }
            
        except HttpError as e:
            logger.error(
                "Failed to get row",
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                row_number=row_number,
                error=str(e)
            )
            raise Exception(f"Failed to get row: {e}")
    
    def get_row_with_headers(
        self, 
        spreadsheet_id: str, 
        sheet_name: str, 
        row_number: int,
        header_row: int = 1
    ) -> Dict[str, Any]:
        """
        Get row data with column headers as keys.
        
        Fetches both the header row and the target row in a single batch request,
        then maps the values to their corresponding headers.
        
        Args:
            spreadsheet_id: The Google Spreadsheet ID
            sheet_name: Name of the sheet tab
            row_number: Row number to retrieve (1-indexed)
            header_row: Row containing column headers (default: 1)
            
        Returns:
            Dict with row data including key-value pairs based on headers:
            {
                "row_number": 5,
                "values": ["John", "Doe", "john@example.com"],
                "headers": ["First Name", "Last Name", "Email"],
                "data": {
                    "First Name": "John",
                    "Last Name": "Doe",
                    "Email": "john@example.com"
                },
                "spreadsheet_id": "...",
                "sheet_name": "Sheet1"
            }
            
        Raises:
            Exception: If row cannot be fetched
        """
        try:
            sheets = self._get_sheets_service()
            
            # Fetch both header row and data row in one batch request
            ranges = [
                f"'{sheet_name}'!{header_row}:{header_row}",
                f"'{sheet_name}'!{row_number}:{row_number}"
            ]
            
            result = sheets.spreadsheets().values().batchGet(
                spreadsheetId=spreadsheet_id,
                ranges=ranges
            ).execute()
            
            value_ranges = result.get('valueRanges', [])
            
            # Extract headers and values
            headers = value_ranges[0].get('values', [[]])[0] if len(value_ranges) > 0 and value_ranges[0].get('values') else []
            values = value_ranges[1].get('values', [[]])[0] if len(value_ranges) > 1 and value_ranges[1].get('values') else []
            
            # Create key-value mapping (header -> value)
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = values[i] if i < len(values) else ""
            
            logger.info(
                "Row with headers retrieved",
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                row_number=row_number,
                header_row=header_row,
                columns=len(values),
                headers_count=len(headers)
            )
            
            return {
                "row_number": row_number,
                "header_row": header_row,
                "values": values,
                "headers": headers,
                "data": row_dict,
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name
            }
            
        except HttpError as e:
            logger.error(
                "Failed to get row with headers",
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                row_number=row_number,
                error=str(e)
            )
            raise Exception(f"Failed to get row: {e}")

