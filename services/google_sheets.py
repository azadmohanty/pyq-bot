from typing import Dict, Tuple
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os
import json
import logging

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def _get_creds() -> Credentials:
    try:
        # First try to use environment variables (for production/Vercel)
        client_type = os.getenv("GOOGLE_CLIENT_TYPE")
        project_id = os.getenv("GOOGLE_PROJECT_ID")
        private_key = os.getenv("GOOGLE_PRIVATE_KEY")
        client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
        
        if client_type and project_id and private_key and client_email:
            logger.info("Using Google API credentials from environment variables")
            
            # Replace escaped newlines with actual newlines in private key
            if "\\n" in private_key:
                private_key = private_key.replace("\\n", "\n")
            
            # Create credentials dict from environment variables
            creds_dict = {
                "type": client_type,
                "project_id": project_id,
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
                "private_key": private_key,
                "client_email": client_email,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "auth_uri": os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL", 
                                                     "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL")
            }
            
            # Create credentials from dict
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            return creds
        
        # Fallback to local credentials file
        client_secret_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "client_secret.json")
        if not os.path.exists(client_secret_path):
            raise FileNotFoundError(
                "client_secret.json not found and environment variables not set. Please add this file to the project root.\n"
                "See GOOGLE_SHEETS_SETUP.md for instructions or run setup_google_api.py for assistance."
            )
        
        # Create credentials from service account file
        creds = Credentials.from_service_account_file(
            client_secret_path, scopes=SCOPES
        )
        
        return creds
    except Exception as e:
        logger.error(f"Error getting credentials: {e}")
        raise

def load_code_map(spreadsheet_id: str, range_a1: str) -> Dict[str, Tuple[str, str]]:
    """
    Read the sheet range and return a dict: subject_code -> (subject_name, url).
    Sheet must have columns: subject_code | subject_name | url, starting at A2.
    """
    creds = _get_creds()
    service = build("sheets", "v4", credentials=creds)
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_a1
    ).execute().get("values", [])
    out: Dict[str, Tuple[str, str]] = {}
    for row in values:
        if len(row) >= 3:
            code = row[0].strip()
            name = row[1].strip()
            url = row[2].strip() if len(row) > 2 else ""
            if code and name:
                out[code] = (name, url)
        elif len(row) == 2:
            # Handle case where URL might be missing
            code = row[0].strip()
            name = row[1].strip()
            if code and name:
                out[code] = (name, "")
    return out