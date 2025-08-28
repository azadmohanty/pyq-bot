from typing import Dict, List, Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def list_subjects(code_map: Dict[str, Tuple[str, str]], page: int = 0, page_size: int = 15) -> str:
    """
    Format a list of subjects with monospace codes and underscored names.
    Supports pagination if needed.
    
    Args:
        code_map: Dictionary mapping subject codes to (name, url) tuples
        page: Current page number (0-indexed)
        page_size: Number of items per page
        
    Returns:
        Formatted string with subject codes and names
    """
    if not code_map:
        return "No subjects available."
    
    # Convert to list for pagination
    items = list(code_map.items())
    
    # Sort items by subject code for consistent display
    items.sort(key=lambda x: x[0])
    
    # Calculate pagination
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(items))
    current_items = items[start_idx:end_idx]
    
    # Format each subject
    lines = []
    for code, (name, _) in current_items:
        # Escape special characters for MarkdownV2
        escaped_code = escape_markdown(code)
        escaped_name = escape_markdown(name)
        # Format with monospace code and underscored name - ensure code is in monospace format
        lines.append(f"`{escaped_code}` _{escaped_name}_")
    
    # Add pagination info if needed
    total_pages = (len(items) + page_size - 1) // page_size
    if total_pages > 1:
        lines.append(f"\nPage {page + 1}/{total_pages}")
    
    return "\n".join(lines)

def create_year_keyboard() -> InlineKeyboardMarkup:
    """
    Create a keyboard with year buttons in two rows.
    """
    keyboard = [
        [
            InlineKeyboardButton("1st Year", callback_data="year:1"),
            InlineKeyboardButton("2nd Year", callback_data="year:2"),
        ],
        [
            InlineKeyboardButton("3rd Year", callback_data="year:3"),
            InlineKeyboardButton("4th Year", callback_data="year:4"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_branch_keyboard(year: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard with branch buttons and a back button.
    
    Args:
        year: The year number (2, 3, or 4)
        
    Returns:
        Keyboard markup with branch buttons
    """
    # Updated branch list based on CSV data
    if year == 2:
        branches = [
            ("AE", f"y{year}:branch:AE"),
            ("MME", f"y{year}:branch:MME"),
            ("CSE", f"y{year}:branch:CSE"),
            ("ETC", f"y{year}:branch:ETC"),
            ("ME", f"y{year}:branch:ME"),
            ("EE", f"y{year}:branch:EE"),
            ("CE", f"y{year}:branch:CE"),
            ("CHE", f"y{year}:branch:CHE"),
        ]
    elif year == 1:
        # First year has no branches, just return to year selection
        keyboard = [[InlineKeyboardButton("Back", callback_data="back_to_years")]]
        return InlineKeyboardMarkup(keyboard)
    else:
        branches = [
            ("CSE", f"y{year}:branch:CSE"),
            ("ECE", f"y{year}:branch:ECE"),
            ("ME", f"y{year}:branch:ME"),
            ("CE", f"y{year}:branch:CE"),
            ("EE", f"y{year}:branch:EE"),
        ]
    
    # Create buttons in rows of 2-3
    keyboard = []
    row = []
    for i, (name, callback) in enumerate(branches):
        row.append(InlineKeyboardButton(name, callback_data=callback))
        if len(row) == 3 or i == len(branches) - 1:
            keyboard.append(row.copy())  # Use copy to avoid reference issues
            row = []
    
    # Add back button in a separate row
    keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_years")])
    
    return InlineKeyboardMarkup(keyboard)

def create_pagination_keyboard(page: int, total_pages: int, prefix: str) -> Optional[InlineKeyboardMarkup]:
    """
    Create pagination buttons (Prev/Next) for subject lists.
    
    Args:
        page: Current page (0-indexed)
        total_pages: Total number of pages
        prefix: Prefix for callback data (e.g., 'y1:' or 'y2:branch:CSE:')
        
    Returns:
        Keyboard markup with pagination buttons, or None if no pagination needed
    """
    if total_pages <= 1:
        return None
    
    keyboard = [[]]
    if page > 0:
        keyboard[0].append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}page:{page-1}"))
    if page < total_pages - 1:
        keyboard[0].append(InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}page:{page+1}"))
    
    # Add a back button
    if prefix.startswith('y'):
        if ':branch:' in prefix:
            # Back to branch selection
            year = prefix[1:2]
            keyboard.append([InlineKeyboardButton("Back to Branches", callback_data=f"year:{year}")])
        else:
            # Back to year selection
            keyboard.append([InlineKeyboardButton("Back to Years", callback_data="back_to_years")])
    
    return InlineKeyboardMarkup(keyboard)

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram's MarkdownV2 format.
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def parse_csv_data(csv_path: str, year: int, fallback_data: Dict[str, Tuple[str, str]] = None) -> Dict[str, Dict[str, Tuple[str, str]]]:
    """
    Parse a CSV file and return a dictionary of branch -> subject code -> (subject name, url)
    
    Args:
        csv_path: Path to the CSV file
        year: Year number (1 or 2)
        fallback_data: Fallback data to use if CSV file is not found or has errors
        
    Returns:
        Dictionary mapping branch to subject code map
    """
    import csv
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    branch_data = {}
    
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        # Return fallback data if provided
        if fallback_data:
            if year == 1:
                # For first year, we need to wrap the fallback data in a branch dictionary
                return {"common": fallback_data}
            return fallback_data
        else:
            # Return empty data if no fallback provided
            return {}
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and row[0] == "Branch" and row[1] == "Subject_Code" and row[2] == "Subject_Name":
                    # This is a header row, the next row will have the branch
                    continue
                elif len(row) >= 3:
                    branch = row[0]
                    subject_code = row[1]
                    subject_name = row[2]
                    
                    # Skip empty rows
                    if not branch or not subject_code or not subject_name:
                        continue
                    
                    # If this is a new branch, create a new entry
                    if branch not in branch_data:
                        branch_data[branch] = {}
                    
                    # Add the subject to the branch data with a placeholder URL
                    # In a real implementation, you would use actual URLs
                    url = f"https://drive.google.com/drive/folders/{year}-{branch.lower()}-{subject_code.lower()}"
                    branch_data[branch][subject_code] = (subject_name, url)
    except Exception as e:
        logger.exception(f"Error parsing CSV for year {year}: {e}")
        # Return fallback data if provided
        if fallback_data:
            if year == 1:
                # For first year, we need to wrap the fallback data in a branch dictionary
                return {"common": fallback_data}
            return fallback_data
        else:
            # Return empty data if no fallback provided
            return {}
    
    return branch_data

def parse_first_year_csv(csv_path: str, fallback_data: Dict[str, Tuple[str, str]] = None) -> Dict[str, Dict[str, Tuple[str, str]]]:
    """
    Parse the first year CSV file and return a dictionary with common branch -> subject code -> (subject name, url)
    
    Args:
        csv_path: Path to the CSV file
        fallback_data: Fallback data to use if CSV file is not found or has errors
        
    Returns:
        Dictionary with common branch mapping to subject code map
    """
    return parse_csv_data(csv_path, 1, fallback_data)

def parse_second_year_csv(csv_path: str) -> Dict[str, Dict[str, Tuple[str, str]]]:
    """
    Parse the second year CSV file and return a dictionary of branch -> subject code -> (subject name, url)
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary mapping branch to subject code map
    """
    # Fallback data for second year
    fallback_data = {
        "CSE": {"23CS2001": ("Data Structures", "https://drive.google.com/drive/folders/cse-23cs2001")},
        "ECE": {"23EC2001": ("Digital Electronics", "https://drive.google.com/drive/folders/ece-23ec2001")},
        "ME": {"23ME2001": ("Thermodynamics", "https://drive.google.com/drive/folders/me-23me2001")},
        "CE": {"23CE2001": ("Structural Analysis", "https://drive.google.com/drive/folders/ce-23ce2001")},
        "EE": {"23EE2001": ("Electrical Machines", "https://drive.google.com/drive/folders/ee-23ee2001")},
        "AE": {"23AE2001": ("Aerodynamics", "https://drive.google.com/drive/folders/ae-23ae2001")},
        "MME": {"23MM2001": ("Materials Science", "https://drive.google.com/drive/folders/mme-23mm2001")},
        "ETC": {"23ET2001": ("Communication Systems", "https://drive.google.com/drive/folders/etc-23et2001")},
        "CHE": {"23CH2001": ("Chemical Process", "https://drive.google.com/drive/folders/che-23ch2001")},
    }
    
    return parse_csv_data(csv_path, 2, fallback_data)

def parse_master_subject_url_csv(csv_path: str) -> Dict[str, Tuple[str, str]]:
    """
    Parse the Master_SubCode_And_URL CSV file and return a dictionary of subject code -> (subject name, url)
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary mapping subject code to (subject name, url) tuple
    """
    import csv
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.error(f"Master subject URL CSV file not found at {csv_path}")
        return {}
    
    subject_url_map = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader, None)
            
            for row in reader:
                if len(row) >= 4:  # Year, Subject_Name, Subject_Code, URL
                    year = row[0].strip()
                    subject_name = row[1].strip()
                    subject_code = row[2].strip()
                    url = row[3].strip()
                    
                    if subject_code and subject_name and url:
                        subject_url_map[subject_code] = (subject_name, url)
        
        logger.info(f"Successfully loaded {len(subject_url_map)} subjects from master URL CSV")
    except Exception as e:
        logger.exception(f"Error parsing master subject URL CSV: {e}")
    
    return subject_url_map