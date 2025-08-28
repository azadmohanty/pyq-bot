from config import INTRO_TEXT
from utils.message_formatting import list_subjects, create_year_keyboard, create_branch_keyboard, parse_second_year_csv, parse_first_year_csv
from utils.firebase_db import get_subjects_by_year_branch
from telegram.ext import CallbackQueryHandler, ApplicationBuilder
from telegram import Update
from typing import Dict, Tuple, Optional
import logging
import os

logger = logging.getLogger(__name__)

# In-memory cache for subject data by year and branch
SUBJECT_CODES = {
    # First year is common for all branches
    1: {"common": None},
    # Second year has branch-specific subjects from CSV
    2: {
        "AE": None, "MME": None, "CSE": None, "ETC": None, 
        "ME": None, "EE": None, "CE": None, "CHE": None
    },
    # Other years have branch-specific subjects
    3: {"CSE": None, "ECE": None, "ME": None, "CE": None, "EE": None},
    4: {"CSE": None, "ECE": None, "ME": None, "CE": None, "EE": None},
}

# Path to the CSV files
FIRST_YEAR_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "CONTEXT 1ST YER SUB.csv")
SECOND_YEAR_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "CONTEXT 2ND YER SUB.csv")

# Check if the CSV files exist and log warnings if they don't
if not os.path.exists(FIRST_YEAR_CSV_PATH):
    logger.warning(f"First year CSV file not found at {FIRST_YEAR_CSV_PATH}. Will use fallback data.")

if not os.path.exists(SECOND_YEAR_CSV_PATH):
    logger.warning(f"Second year CSV file not found at {SECOND_YEAR_CSV_PATH}. Will use fallback data.")

# Load data from CSV
FIRST_YEAR_DATA_CSV = None
SECOND_YEAR_DATA = None

# First year fallback data (used if CSV file is not found)
FIRST_YEAR_DATA = {
    "23BS1001": ("Mathematics-I", "https://drive.google.com/drive/folders/first-year-math1"),
    "RMA2A001": ("Mathematics-II", "https://drive.google.com/drive/folders/first-year-math2"),
    "23BS1002": ("Physics", "https://drive.google.com/drive/folders/first-year-physics"),
    "23BS1003": ("Chemistry", "https://drive.google.com/drive/folders/first-year-chemistry"),
    "23ES1001": ("Basic Electrical Engineering", "https://drive.google.com/drive/folders/first-year-bee"),
    "23ES1002": ("Basic Electronics", "https://drive.google.com/drive/folders/first-year-be"),
    "RBM1B001": ("Basic Mechanical Engineering", "https://drive.google.com/drive/folders/first-year-bme"),
    "RBC1B002": ("Basic Civil Engineering", "https://drive.google.com/drive/folders/first-year-bce"),
    "23ES1003": ("Programming in C and Data Structures", "https://drive.google.com/drive/folders/first-year-c-ds"),
    "REM2B001": ("Engineering Mechanics", "https://drive.google.com/drive/folders/first-year-em"),
    "RCE1E001": ("Communicative English", "https://drive.google.com/drive/folders/first-year-ce"),
    "23HS1001": ("Universal Human Values", "https://drive.google.com/drive/folders/first-year-uhv"),
}

# Dummy data for testing - replace with actual data from Google Sheets later
DUMMY_DATA = {
    # First year data (can be used as fallback if Google Sheets fails)
    "1:common": FIRST_YEAR_DATA,
    
    # Sample data for 3rd year
    "3:CSE": {"23CS3001": ("Operating Systems", "https://drive.google.com/drive/folders/dummy-os")},
    "3:ECE": {"23EC3001": ("Communication Systems", "https://drive.google.com/drive/folders/dummy-cs")},
    "3:ME": {"23ME3001": ("Fluid Mechanics", "https://drive.google.com/drive/folders/dummy-fm")},
    "3:CE": {"23CE3001": ("Geotechnical Engineering", "https://drive.google.com/drive/folders/dummy-ge")},
    "3:EE": {"23EE3001": ("Power Systems", "https://drive.google.com/drive/folders/dummy-ps")},
    
    # Sample data for 4th year
    "4:CSE": {"23CS4001": ("Machine Learning", "https://drive.google.com/drive/folders/dummy-ml")},
    "4:ECE": {"23EC4001": ("VLSI Design", "https://drive.google.com/drive/folders/dummy-vlsi")},
    "4:ME": {"23ME4001": ("Robotics", "https://drive.google.com/drive/folders/dummy-robotics")},
    "4:CE": {"23CE4001": ("Transportation Engineering", "https://drive.google.com/drive/folders/dummy-te")},
    "4:EE": {"23EE4001": ("Control Systems", "https://drive.google.com/drive/folders/dummy-cs")},
}

async def start_handler(update, context):
    """
    Show the year selection keyboard.
    """
    # Reset any existing state
    if hasattr(context.user_data, "year"):
        del context.user_data["year"]
    if hasattr(context.user_data, "branch"):
        del context.user_data["branch"]
    
    # Send welcome message with year selection keyboard
    welcome_text = "🎓 Welcome to the PYQ Bot! Please select your year:"
    await update.message.reply_text(
        welcome_text,
        reply_markup=create_year_keyboard()
    )

async def year_callback_handler(update: Update, context):
    """
    Handle year selection callback.
    """
    query = update.callback_query
    await query.answer()  # Answer to remove the loading spinner
    
    # Extract year from callback data
    callback_data = query.data
    if callback_data.startswith("year:"):
        year = int(callback_data.split(":")[1])
        context.user_data["year"] = year
        
        if year == 1:
            # First year: show subject list directly
            await show_subject_list(update, context, year, "common")
        else:
            # Other years: show branch selection
            await query.edit_message_text(
                f"🎓 You selected {year}st Year. Please select your branch:",
                reply_markup=create_branch_keyboard(year)
            )
    elif callback_data == "back_to_years":
        # Go back to year selection
        if "year" in context.user_data:
            del context.user_data["year"]
        if "branch" in context.user_data:
            del context.user_data["branch"]
        
        await query.edit_message_text(
            "🎓 Please select your year:",
            reply_markup=create_year_keyboard()
        )

async def branch_callback_handler(update: Update, context):
    """
    Handle branch selection callback.
    """
    query = update.callback_query
    await query.answer()  # Answer to remove the loading spinner
    
    # Extract year and branch from callback data
    callback_data = query.data
    if callback_data.startswith("y") and ":branch:" in callback_data:
        parts = callback_data.split(":")
        year = int(parts[0][1:])  # Extract year from 'y2' format
        branch = parts[2]
        
        context.user_data["year"] = year
        context.user_data["branch"] = branch
        
        # Show subject list for selected year and branch
        await show_subject_list(update, context, year, branch)

async def show_subject_list(update: Update, context, year: int, branch: str):
    """
    Show the subject list for the selected year and branch.
    First tries to fetch data from Firebase, then falls back to CSV or hardcoded data.
    """
    query = update.callback_query
    
    # Try to get data from Firebase first
    try:
        firebase_subjects = await get_subjects_by_year_branch(year, branch)
        if firebase_subjects and len(firebase_subjects) > 0:
            logger.info(f"Successfully loaded {len(firebase_subjects)} subjects from Firebase for year {year}, branch {branch}")
            # Cache the data in SUBJECT_CODES
            SUBJECT_CODES[year][branch] = firebase_subjects
            code_map = firebase_subjects
            # Skip the CSV loading since we have Firebase data
            logger.info("Using Firebase data instead of CSV")
        else:
            logger.info(f"No data found in Firebase for year {year}, branch {branch}, falling back to CSV")
            # Continue with CSV fallback
            code_map = None
    except Exception as e:
        logger.exception(f"Error loading data from Firebase: {e}")
        logger.info("Falling back to CSV data")
        code_map = None
    
    # If Firebase didn't provide data, load from CSV or use fallback
    if code_map is None:
        # Load subject data if not already cached
        if year == 1:
            # First year: load from CSV file or use fallback
            global FIRST_YEAR_DATA_CSV
            
            # Load the CSV data if not already loaded
            if SUBJECT_CODES[1]["common"] is None:
                try:
                    # First try to load from CSV
                    if FIRST_YEAR_DATA_CSV is None:
                        logger.info("Loading first year data from CSV")
                        FIRST_YEAR_DATA_CSV = parse_first_year_csv(FIRST_YEAR_CSV_PATH, FIRST_YEAR_DATA)
                        logger.info("Successfully loaded first year data from CSV")
                    
                    # Cache the data in SUBJECT_CODES
                    if "common" in FIRST_YEAR_DATA_CSV:
                        SUBJECT_CODES[1]["common"] = FIRST_YEAR_DATA_CSV["common"]
                    else:
                        logger.warning("No 'common' branch found in first year CSV, falling back to hardcoded data")
                        SUBJECT_CODES[1]["common"] = FIRST_YEAR_DATA
                except Exception as e:
                    logger.exception(f"Error loading first year data from CSV: {e}")
                    logger.info("Falling back to hardcoded first year data")
                    SUBJECT_CODES[1]["common"] = FIRST_YEAR_DATA
            
            code_map = SUBJECT_CODES[1]["common"]
            if not code_map:
                logger.error("No subject data available after fallback")
                await query.edit_message_text(
                    "Error loading subject data. Please try again later or contact support."
                )
                return
    elif year == 2 and code_map is None:  # Only proceed if Firebase didn't provide data
        # Second year: load from CSV file
        global SECOND_YEAR_DATA_CSV
        
        # Load the CSV data if not already loaded
        if SUBJECT_CODES[2][branch] is None:
            try:
                # First try to load from CSV
                if SECOND_YEAR_DATA_CSV is None:
                    logger.info("Loading second year data from CSV")
                    SECOND_YEAR_DATA_CSV = parse_second_year_csv(SECOND_YEAR_CSV_PATH)
                    logger.info(f"Successfully loaded second year data for branches: {', '.join(SECOND_YEAR_DATA_CSV.keys())}")
                
                # Cache the data in SUBJECT_CODES
                if branch in SECOND_YEAR_DATA_CSV:
                    SUBJECT_CODES[2][branch] = SECOND_YEAR_DATA_CSV[branch]
                else:
                    logger.warning(f"No '{branch}' branch found in second year CSV")
                    SUBJECT_CODES[2][branch] = {}
            except Exception as e:
                logger.exception(f"Error loading second year data from CSV: {e}")
                SUBJECT_CODES[2][branch] = {}
        
        code_map = SUBJECT_CODES[2][branch]
        if not code_map:
            await query.edit_message_text(
                f"No subjects found for 2nd Year, {branch} branch. Please try another branch or contact support."
            )
            return
    elif code_map is None:  # Only proceed if Firebase didn't provide data
        # Other years: use dummy data for now
        key = f"{year}:{branch}"
        if key in DUMMY_DATA:
            code_map = DUMMY_DATA[key]
        else:
            code_map = {}
    
    # Format the subject list
    instruction = "Click and copy a subject code above, then send only the code here to receive the link.\n"
    
    # Escape special characters for MarkdownV2
    year_suffix = 'ST' if year == 1 else 'ND' if year == 2 else 'RD' if year == 3 else 'TH'
    branch_text = branch if branch != 'common' else ''
    
    # Escape special characters in the text
    from utils.message_formatting import escape_markdown
    escaped_year_suffix = escape_markdown(year_suffix)
    escaped_branch_text = escape_markdown(branch_text)
    escaped_instruction = escape_markdown(instruction)
    
    text = f"📚 *{year}{escaped_year_suffix} YEAR {escaped_branch_text}*\n\n"
    text += list_subjects(code_map)
    # Use raw string for the help text to avoid escape sequence issues
    help_text = escape_markdown("For Instructions /help\n♥️Help Us Grow /donate\nCreated With ♥️ By Someone Like You")
    text += f"\n\n📝 {escaped_instruction}\n🔍 _{help_text}_"
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2"
    )

def register_callback_handlers(app):
    """
    Register all callback handlers.
    """
    app.add_handler(CallbackQueryHandler(year_callback_handler, pattern=r"^year:|^back_to_years$"))
    app.add_handler(CallbackQueryHandler(branch_callback_handler, pattern=r"^y\d:branch:"))
    # Add pagination handler later if needed
