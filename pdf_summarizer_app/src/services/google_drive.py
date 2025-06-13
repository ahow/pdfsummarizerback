import os
import io
import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveService:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """Authenticate and build the Google Drive service."""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file {self.credentials_file} not found. Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        return self.service
    
    def list_files(self, folder_id=None, mime_type='application/pdf', days_back=7):
        """List files in Google Drive, optionally filtered by folder and date."""
        if not self.service:
            self.authenticate()
        
        # Calculate date filter for files added in the last week
        date_filter = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'
        
        # Build query
        query_parts = [f"mimeType='{mime_type}'", f"createdTime >= '{date_filter}'"]
        
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        query = ' and '.join(query_parts)
        
        try:
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, createdTime, webViewLink, size)"
            ).execute()
            
            items = results.get('files', [])
            return items
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def download_file(self, file_id, local_path):
        """Download a file from Google Drive."""
        if not self.service:
            self.authenticate()
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            
            return True
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    
    def upload_file(self, local_path, drive_filename, folder_id=None):
        """Upload a file to Google Drive."""
        if not self.service:
            self.authenticate()
        
        try:
            file_metadata = {'name': drive_filename}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(local_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            return file
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def get_file_info(self, file_id):
        """Get detailed information about a file."""
        if not self.service:
            self.authenticate()
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id,name,createdTime,modifiedTime,webViewLink,size,mimeType'
            ).execute()
            return file
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None

