from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import json
import time

SCOPES = ['https://www.googleapis.com/auth/drive.file']
UPLOAD_TIMEOUT = 600  # 10 minutes timeout for uploads
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def get_credentials():
    try:
        creds_json = os.environ.get('GOOGLE_OAUTH_CREDENTIALS')
        if not creds_json:
            print("Error: GOOGLE_OAUTH_CREDENTIALS environment variable not found")
            return None
        
        print("Got credentials from environment, attempting to parse...")
        try:
            creds_info = json.loads(creds_json)
            if not isinstance(creds_info, dict):
                print("Error: Invalid credentials format")
                return None
        except json.JSONDecodeError as e:
            print(f"Error parsing credentials JSON: {str(e)}")
            return None

        print("Creating credentials object...")
        try:
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            print("Successfully created credentials object")
            return creds
        except Exception as e:
            print(f"Error creating credentials object: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error in get_credentials: {str(e)}")
        return None

def create_drive_service():
    try:
        print("Getting credentials...")
        creds = get_credentials()
        if not creds:
            return None
        print("Building Drive service...")
        service = build('drive', 'v3', credentials=creds)
        print("Drive service created successfully")
        return service
    except Exception as e:
        print(f"Error creating drive service: {str(e)}")
        return None

def create_folder(service, folder_name="LeaseCheck_Files"):
    try:
        print(f"Checking if folder '{folder_name}' exists...")
        response = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
        ).execute()

        if response.get('files'):
            folder_id = response['files'][0]['id']
            print(f"Found existing folder: {folder_name} (ID: {folder_id})")
            return folder_id

        print(f"Creating new folder: {folder_name}")
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = file.get('id')
        print(f'Created new folder: {folder_name} (ID: {folder_id})')
        return folder_id
    except Exception as e:
        print(f"Error creating folder: {str(e)}")
        return None

def upload_file(service, folder_id, file_path, maintain_structure=True, retry_count=0):
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
            
        if maintain_structure:
            rel_path = os.path.relpath(file_path, '.')
            file_name = rel_path.replace('\\', '/')
        else:
            file_name = os.path.basename(file_path)
            
        print(f"Preparing to upload: {file_name}")
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        print(f"Starting upload for {file_name}")
        try:
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f'Successfully uploaded {file_name} (ID: {file.get("id")})')
            return True
            
        except Exception as upload_error:
            print(f"Upload error for {file_name}: {str(upload_error)}")
            if retry_count < MAX_RETRIES:
                print(f"Retrying upload ({retry_count + 1}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
                return upload_file(service, folder_id, file_path, maintain_structure, retry_count + 1)
            return False

    except Exception as e:
        print(f"Error preparing upload for {file_path}: {str(e)}")
        return False

def collect_files():
    files_to_upload = []
    
    # Root files
    root_files = ['main.py', 'pyproject.toml', 'google_drive_upload.py', '.replit', 'README.md']
    for file in root_files:
        if os.path.exists(file):
            files_to_upload.append(file)
    
    # Directory files
    directories = [
        'leasecheck/templates',
        'leasecheck/static/css',
        'leasecheck/static/images'
    ]
    
    for dir_path in directories:
        if os.path.exists(dir_path):
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    files_to_upload.append(file_path)
    
    return files_to_upload

def main():
    print("\n=== Starting Google Drive upload process ===\n")
    
    service = create_drive_service()
    if not service:
        print("Failed to create Drive service")
        return False

    folder_id = create_folder(service)
    if not folder_id:
        print("Failed to create folder")
        return False

    print("\n=== Beginning file upload ===\n")
    
    files_to_upload = collect_files()
    total_files = len(files_to_upload)
    uploaded_files = []
    failed_files = []
    
    print(f"Total files to upload: {total_files}\n")
    
    for index, file_path in enumerate(files_to_upload, 1):
        print(f"\nProcessing file {index}/{total_files}: {file_path}")
        if upload_file(service, folder_id, file_path, maintain_structure=True):
            uploaded_files.append(file_path)
        else:
            failed_files.append(file_path)
            
        # Print progress summary every 5 files
        if index % 5 == 0 or index == total_files:
            print(f"\nProgress Summary:")
            print(f"Files processed: {index}/{total_files}")
            print(f"Successfully uploaded: {len(uploaded_files)}")
            print(f"Failed uploads: {len(failed_files)}")
    
    print("\n=== Upload Summary ===")
    print(f"Total files processed: {total_files}")
    print(f"Successfully uploaded: {len(uploaded_files)}")
    print(f"Failed uploads: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for file in failed_files:
            print(f"- {file}")
        return False
    
    print("\n=== All files uploaded successfully! ===")
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
