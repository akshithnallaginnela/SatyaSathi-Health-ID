import os
import uuid
import firebase_admin
from firebase_admin import credentials, storage

def get_firebase_app():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_JSON")
        bucket_url = os.getenv("FIREBASE_STORAGE_BUCKET")
        
        if cred_path and os.path.exists(cred_path) and bucket_url:
            cred = credentials.Certificate(cred_path)
            bucket_name = bucket_url.replace("gs://", "").strip()
            firebase_admin.initialize_app(cred, {
                'storageBucket': bucket_name
            })
        else:
            return None
    return firebase_admin.get_app()

async def upload_file_to_firebase(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Uploads a file to Firebase storage and returns the public URL.
    Falls back to a mock URL if Firebase is not fully configured in .env.
    """
    app = get_firebase_app()
    if not app:
        print("WARNING: Firebase credentials or bucket not configured. Returning mock storage URL.")
        # We can return a mock URL so the app continues to work for demo purposes
        return f"https://mock-firebase-storage.appspot.com/mock_path/{filename}"
    
    bucket = storage.bucket()
    
    # Clean filename and add UUID to prevent overwriting
    safe_filename = filename.replace(" ", "_").replace("/", "-")
    unique_path = f"health_reports/{uuid.uuid4()}_{safe_filename}"
    blob = bucket.blob(unique_path)
    
    blob.upload_from_string(file_bytes, content_type=content_type)
    
    # Make the blob publicly accessible (For MVP/Hackathon ease of use with OCR testing)
    blob.make_public()
    return blob.public_url
