# Import Firebase functionality
from handlers.start_handler import SUBJECT_CODES, DUMMY_DATA, FIRST_YEAR_DATA, FIRST_YEAR_DATA_CSV, SECOND_YEAR_DATA, FIRST_YEAR_CSV_PATH, SECOND_YEAR_CSV_PATH
from utils.message_formatting import parse_first_year_csv, parse_second_year_csv, parse_master_subject_url_csv, escape_markdown
from utils.firebase_db import initialize_firebase, get_subject_data, get_subjects_by_year_branch
import logging
import os

logger = logging.getLogger(__name__)

# Define path to Master_SubCode_And_URL CSV file
MASTER_SUBJECT_URL_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Master_SubCode_And_URL.csv")
# Check if file with space exists (for backward compatibility)
if not os.path.exists(MASTER_SUBJECT_URL_CSV_PATH):
    alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Master_SubCode_And_URL .csv")
    if os.path.exists(alt_path):
        MASTER_SUBJECT_URL_CSV_PATH = alt_path
        logger.info(f"Using alternative path with space: {MASTER_SUBJECT_URL_CSV_PATH}")

# Global variable to store the master subject URL map
MASTER_SUBJECT_URL_MAP = None

# Check if the master subject URL CSV file exists
if not os.path.exists(MASTER_SUBJECT_URL_CSV_PATH):
    logger.warning(f"Master subject URL CSV file not found at {MASTER_SUBJECT_URL_CSV_PATH}")
else:
    logger.info(f"Master subject URL CSV file found at {MASTER_SUBJECT_URL_CSV_PATH}")

# Initialize Firebase when module is loaded
firebase_initialized = initialize_firebase()

async def subject_code_handler(update, context):
    """
    Treat any text message as a subject code and try to look it up.
    First checks Firebase, then the master subject URL map, then falls back to year/branch specific data.
    """
    code = (update.message.text or "").strip()
    
    # First, try to find the subject in Firebase if it's initialized
    if firebase_initialized:
        try:
            logger.info(f"Looking up subject code {code} in Firebase")
            firebase_result = await get_subject_data(code)
            if firebase_result:
                name, url = firebase_result
                # Escape special characters for MarkdownV2
                escaped_code = escape_markdown(code)
                escaped_name = escape_markdown(name)
                escaped_url = escape_markdown(url)
                
                # Format: Bold code, followed by name, then URL on a new line
                await update.message.reply_text(
                    f"📘 *{escaped_code}*: {escaped_name}\n\n🔗 {escaped_url}", 
                    parse_mode="MarkdownV2"
                )
                return
            else:
                logger.info(f"Subject code {code} not found in Firebase, falling back to CSV")
        except Exception as e:
            logger.exception(f"Error retrieving data from Firebase: {e}")
    
    # Second, try to find the subject code in the master subject URL map
    global MASTER_SUBJECT_URL_MAP
    if MASTER_SUBJECT_URL_MAP is None:
        try:
            logger.info("Loading master subject URL data from CSV")
            MASTER_SUBJECT_URL_MAP = parse_master_subject_url_csv(MASTER_SUBJECT_URL_CSV_PATH)
            logger.info(f"Successfully loaded {len(MASTER_SUBJECT_URL_MAP)} subjects from master URL CSV")
        except Exception as e:
            logger.exception(f"Error loading master subject URL data from CSV: {e}")
            MASTER_SUBJECT_URL_MAP = {}
    
    # Check if the code exists in the master subject URL map
    if code in MASTER_SUBJECT_URL_MAP:
        name, url = MASTER_SUBJECT_URL_MAP[code]
        # Escape special characters for MarkdownV2
        escaped_code = escape_markdown(code)
        escaped_name = escape_markdown(name)
        escaped_url = escape_markdown(url)
        
        # Format: Bold code, followed by name, then URL on a new line
        await update.message.reply_text(
            f"📘 *{escaped_code}*: {escaped_name}\n\n🔗 {escaped_url}", 
            parse_mode="MarkdownV2"
        )
        return
    
    # If not found in master map, fall back to year/branch specific data
    # Get the user's selected year and branch if available
    # Handle both proper context objects and dictionary contexts (for testing)
    try:
        year = context.user_data.get("year", 1)  # Default to 1st year
        branch = context.user_data.get("branch", "common")  # Default to common branch
    except AttributeError:
        # For testing or when context is a dictionary
        year = 1  # Default to 1st year
        branch = "common"  # Default to common branch
        logger.info("Using default year and branch due to context not having user_data")
    
    # Determine which code map to use
    if year == 1:
        # First year: use CSV data if available, otherwise use hardcoded data
        code_map = SUBJECT_CODES[1]["common"]
        if not code_map:
            try:
                # Try to load from CSV first
                global FIRST_YEAR_DATA_CSV
                if FIRST_YEAR_DATA_CSV is None:
                    logger.info("Loading first year data from CSV")
                    FIRST_YEAR_DATA_CSV = parse_first_year_csv(FIRST_YEAR_CSV_PATH, FIRST_YEAR_DATA)
                    logger.info("Successfully loaded first year data from CSV")
                
                # Cache the data in SUBJECT_CODES
                if "common" in FIRST_YEAR_DATA_CSV:
                    code_map = FIRST_YEAR_DATA_CSV["common"]
                else:
                    logger.warning("No 'common' branch found in first year CSV, falling back to hardcoded data")
                    code_map = FIRST_YEAR_DATA
                SUBJECT_CODES[1]["common"] = code_map  # Cache the data
            except Exception as e:
                logger.exception(f"Error loading first year data from CSV: {e}")
                logger.info("Falling back to hardcoded first year data")
                code_map = FIRST_YEAR_DATA
                SUBJECT_CODES[1]["common"] = code_map  # Cache the fallback data
                
            # Verify we have data
            if not code_map:
                logger.error("No subject data available after fallback")
                await update.message.reply_text("Error loading subject data. Please try again later or contact support.")
                return
    elif year == 2:
        # Second year: load from CSV file
        global SECOND_YEAR_DATA
        
        # Load the CSV data if not already loaded
        if SECOND_YEAR_DATA is None:
            try:
                logger.info("Loading second year data from CSV")
                SECOND_YEAR_DATA = parse_second_year_csv(SECOND_YEAR_CSV_PATH)
                logger.info(f"Successfully loaded second year data for branches: {', '.join(SECOND_YEAR_DATA.keys())}")
                
                # Cache the data in SUBJECT_CODES
                for branch_name, branch_data in SECOND_YEAR_DATA.items():
                    SUBJECT_CODES[2][branch_name] = branch_data
            except Exception as e:
                logger.exception(f"Error loading second year data from CSV: {e}")
        
        # Get the subject data for the selected branch
        if branch in SUBJECT_CODES[2] and SUBJECT_CODES[2][branch] is not None:
            code_map = SUBJECT_CODES[2][branch]
        else:
            logger.error(f"No subject data available for branch {branch}")
            await update.message.reply_text(f"Error loading subject data for {branch}. Please try again later or contact support.")
            return
    else:
        # Other years: use dummy data for now
        key = f"{year}:{branch}"
        if key in DUMMY_DATA:
            code_map = DUMMY_DATA[key]
        else:
            code_map = {}
    
    # Look up the code
    if code in code_map:
        name, url = code_map[code]
        # Escape special characters for MarkdownV2
        escaped_code = escape_markdown(code)
        escaped_name = escape_markdown(name)
        escaped_url = escape_markdown(url)
        
        # Format: Bold code, followed by name, then URL on a new line
        await update.message.reply_text(
            f"*{escaped_code}*: {escaped_name}\n\n{escaped_url}", 
            parse_mode="MarkdownV2"
        )
    else:
        # Try to find the code in all available code maps
        found = False
        for y in range(1, 5):
            if y == 1:
                branches = ["common"]
            elif y == 2:
                # Use branches from second year CSV
                branches = list(SUBJECT_CODES[2].keys())
            else:
                branches = ["CSE", "ECE", "ME", "CE", "EE"]
            
            for b in branches:
                if y == 1:
                    cm = SUBJECT_CODES[1]["common"]
                elif y == 2 and b in SUBJECT_CODES[2] and SUBJECT_CODES[2][b] is not None:
                    cm = SUBJECT_CODES[2][b]
                else:
                    # For years 3 and 4, use dummy data
                    key = f"{y}:{b}"
                    cm = DUMMY_DATA.get(key, {})
                
                if code in cm:
                    name, url = cm[code]
                    # Escape special characters for MarkdownV2
                    escaped_code = escape_markdown(code)
                    escaped_name = escape_markdown(name)
                    escaped_url = escape_markdown(url)
                    year_suffix = 'st' if y == 1 else 'nd' if y == 2 else 'rd' if y == 3 else 'th'
                    branch_text = b if b != 'common' else ''
                    
                    # Escape year_suffix and branch_text for MarkdownV2
                    escaped_year_suffix = escape_markdown(year_suffix)
                    escaped_branch_text = escape_markdown(branch_text)
                    
                    # Format: Bold code, followed by name, then URL on a new line
                    await update.message.reply_text(
                        f"📘 *{escaped_code}*: {escaped_name}\n\n🔗 {escaped_url}\n\n📌 _Note: This subject is from {y}{escaped_year_suffix} Year {escaped_branch_text}_",
                        parse_mode="MarkdownV2"
                    )
                    found = True
                    break
            
            if found:
                break
        
        if not found:
            # Code not found in any year/branch
            # Use raw string for MarkdownV2 formatting
            await update.message.reply_text(
                r"❌ Unknown code\. Use /start to view the subject list and copy a valid subject code\.",
                parse_mode="MarkdownV2"
            )