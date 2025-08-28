import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
import json
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

# Initialize Firebase
def initialize_firebase():
    """
    Initialize Firebase with service account credentials.
    Supports both local file and environment variables.
    """
    try:
        # First, try to use environment variables (for production/Vercel)
        firebase_type = os.getenv("FIREBASE_TYPE")
        firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
        firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        
        if firebase_type and firebase_project_id and firebase_private_key:
            # Create credentials from environment variables
            logger.info("Using Firebase credentials from environment variables")
            
            # Replace escaped newlines with actual newlines in private key
            if "\\n" in firebase_private_key:
                firebase_private_key = firebase_private_key.replace("\\n", "\n")
            
            cred_dict = {
                "type": firebase_type,
                "project_id": firebase_project_id,
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": firebase_private_key,
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", 
                                                      "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully using environment variables")
            return True
            
        # Fallback to local credentials file
        cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "firebase-credentials.json")
        
        if not os.path.exists(cred_path):
            logger.warning("Firebase credentials file not found and environment variables not set. Using CSV fallback.")
            return False
            
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully using local credentials file")
        return True
    except Exception as e:
        logger.exception(f"Error initializing Firebase: {e}")
        return False

# Get Firestore database instance
def get_db():
    """
    Get Firestore database instance if Firebase is initialized.
    """
    try:
        return firestore.client()
    except Exception as e:
        logger.exception(f"Error getting Firestore client: {e}")
        return None

# Subject data operations
async def get_subject_data(code: str) -> Optional[Tuple[str, str]]:
    """
    Get subject data (name, URL) from Firestore.
    
    Args:
        code: Subject code to look up
        
    Returns:
        Tuple of (name, URL) if found, None otherwise
    """
    db = get_db()
    if not db:
        return None
        
    try:
        doc_ref = db.collection('subjects').document(code)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return (data.get('name', ''), data.get('url', ''))
        return None
    except Exception as e:
        logger.exception(f"Error getting subject data from Firestore: {e}")
        return None

async def get_subjects_by_year_branch(year: int, branch: str) -> Optional[Dict[str, Tuple[str, str]]]:
    """
    Get all subjects for a specific year and branch from Firestore.
    
    Args:
        year: Year (1-4)
        branch: Branch code (e.g., 'CSE', 'common')
        
    Returns:
        Dictionary mapping subject codes to (name, URL) tuples if found, None otherwise
    """
    db = get_db()
    if not db:
        logger.warning("Firebase not initialized, cannot fetch subjects by year/branch")
        return None
        
    try:
        # Query subjects collection where year and branch match
        query = db.collection('subjects').where('year', '==', year).where('branch', '==', branch)
        docs = query.stream()
        
        result = {}
        for doc in docs:
            data = doc.to_dict()
            subject_code = doc.id
            subject_name = data.get('name', '')
            subject_url = data.get('url', '')
            result[subject_code] = (subject_name, subject_url)
        
        logger.info(f"Found {len(result)} subjects for year {year}, branch {branch} in Firebase")
        return result
    except Exception as e:
        logger.exception(f"Error getting subjects by year/branch from Firestore: {e}")
        return None
    """
    Get all subjects for a specific year and branch.
    
    Args:
        year: Year (1, 2, 3, 4)
        branch: Branch code (CSE, ECE, etc.)
        
    Returns:
        Dictionary mapping subject codes to (name, URL) tuples
    """
    db = get_db()
    if not db:
        return {}
        
    try:
        # Query subjects by year and branch
        query = db.collection('subjects').where('year', '==', year)
        
        if year != '1':  # First year is common
            query = query.where('branch', '==', branch)
            
        docs = query.stream()
        
        result = {}
        for doc in docs:
            data = doc.to_dict()
            result[doc.id] = (data.get('name', ''), data.get('url', ''))
            
        return result
    except Exception as e:
        logger.exception(f"Error getting subjects by year/branch from Firestore: {e}")
        return {}

async def get_all_subjects() -> Dict[str, Tuple[str, str]]:
    """
    Get all subjects from Firestore.
    
    Returns:
        Dictionary mapping subject codes to (name, URL) tuples
    """
    db = get_db()
    if not db:
        return {}
        
    try:
        docs = db.collection('subjects').stream()
        
        result = {}
        for doc in docs:
            data = doc.to_dict()
            result[doc.id] = (data.get('name', ''), data.get('url', ''))
            
        return result
    except Exception as e:
        logger.exception(f"Error getting all subjects from Firestore: {e}")
        return {}

# Data migration function (CSV to Firebase)
def migrate_csv_to_firebase(csv_path: str) -> bool:
    """
    Migrate data from CSV to Firebase.
    
    Args:
        csv_path: Path to CSV file with subject data
        
    Returns:
        True if migration successful, False otherwise
    """
    import csv
    
    db = get_db()
    if not db:
        return False
        
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            batch = db.batch()
            count = 0
            
            for row in reader:
                if len(row) >= 3:  # Ensure row has at least code, name, URL
                    code = row[0].strip()
                    name = row[1].strip()
                    url = row[2].strip()
                    
                    # Extract year and branch from code (if possible)
                    year = '1'  # Default
                    branch = 'common'  # Default
                    
                    if len(code) >= 4 and code[0:2].isdigit():
                        year = code[0]
                        
                        # Try to determine branch from code
                        if 'CS' in code:
                            branch = 'CSE'
                        elif 'EC' in code or 'ET' in code:
                            branch = 'ECE'
                        elif 'ME' in code:
                            branch = 'ME'
                        elif 'CE' in code:
                            branch = 'CE'
                        elif 'EE' in code:
                            branch = 'EE'
                        # Add more branch mappings as needed
                    
                    # Create document
                    doc_ref = db.collection('subjects').document(code)
                    batch.set(doc_ref, {
                        'name': name,
                        'url': url,
                        'year': year,
                        'branch': branch
                    })
                    
                    count += 1
                    
                    # Commit in batches of 500
                    if count % 500 == 0:
                        batch.commit()
                        batch = db.batch()
            
            # Commit any remaining documents
            if count % 500 != 0:
                batch.commit()
                
            logger.info(f"Migrated {count} subjects to Firebase")
            return True
    except Exception as e:
        logger.exception(f"Error migrating CSV to Firebase: {e}")
        return False