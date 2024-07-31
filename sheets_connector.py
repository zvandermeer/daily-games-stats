import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]

# Starting columns for each game
class Game():
    CONNECTIONS = 'C'
    WORDLE = 'J'
    MINI = 'M'
    WAFFLE = 'P'
    DELUXE = 'R'
    MINI_SQUARDLE = 'U'
    BIG_SQUARDLE = 'W'

# Create a new set of rows for the new day
def new_day(row, puzzleDate):
    values = [[puzzleDate.strftime("%m/%d/%Y"), "Olivia"], ["", "Zoey"]]

    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!A{row}:B{row+1}",
        "USER_ENTERED",
        values
    )

# Find the row to update from the given puzzle date
def find_row(puzzleDate):
    SERVICE_ACCOUNT_FILE = "service_account_credentials.json"
    credentials = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE
    )

    try:
        service = build('sheets', 'v4', credentials=credentials)
        
        # Get all existing dates in the sheet
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A:A", valueRenderOption="UNFORMATTED_VALUE")
            .execute()
        )
        values = result.get("values")

        # Calculate how many days after the last existing row this
        # puzzle was played
        epoch = datetime(1900, 1, 1)
        last_day = epoch + timedelta(days=values[-1][0] - 2)
        delta = (puzzleDate - last_day).days

        if delta == 0:
            return len(values)

        # If not the last day in the table, create a new day and return that row
        else:
            row = len(values) + (delta * 2)
            new_day(row, puzzleDate)
            return row

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

# Wrapper to simplify updating raw values in the spreadsheet
def update_raw_values(spreadsheet_id, range_name, value_input_option, values):
    SERVICE_ACCOUNT_FILE = "service_account_credentials.json"
    credentials = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE
    )

    try:
        # Set values in the spreadsheet according to given parameters
        service = build('sheets', 'v4', credentials=credentials)
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
    
def update_score(game, score, player, puzzleDate):
    # If a specific game is worked on together, this value can be changed
    # according to the game passed
    collaborate = 'N'

    # Set values to update in the spreadsheet
    values = [[score, collaborate]]

    # Find the row to update
    row = find_row(puzzleDate)

    # Update the values on the sheet
    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{game}{row+player}:{chr(ord(game)+1)}{row+player}",
        "USER_ENTERED",
        values
    )

# Update scores for connections specifically
def update_connections(guesses, order, player, puzzleDate):
    # Determine the order each category was guessed
    try:
        yellowPos = str(order.index("yellow")+1)
    except ValueError:
        yellowPos = "-"

    try:
        greenPos = str(order.index("green")+1)
    except ValueError:
        greenPos = "-"

    try:
        bluePos = str(order.index("blue")+1)
    except ValueError:
        bluePos = "-"

    try:
        purplePos = str(order.index("purple")+1)
    except ValueError:
        purplePos = "-"

    # Set values to update in the spreadsheet
    values = [[guesses, yellowPos, greenPos, bluePos, purplePos, "Worked together"]]

    # Find the row to update
    row = find_row(puzzleDate)

    # Update the values on the sheet
    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{Game.CONNECTIONS}{row+player}:{chr(ord(Game.CONNECTIONS)+5)}{row+player}",
        "USER_ENTERED",
        values
    )

def update_deluxe(stars, swaps, player, puzzleDate):
    values = [[stars, swaps]]

    row = find_row(puzzleDate)

    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{Game.DELUXE}{row+player}:{chr(ord(Game.DELUXE)+1)}{row+player}",
        "USER_ENTERED",
        values
    )

def update_squardle(game, bonusWords, extraData, player, puzzleDate):
    values = [[bonusWords, extraData]]

    row = find_row(puzzleDate)

    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{game}{row+player}:{chr(ord(game)+1)}{row+player}",
        "USER_ENTERED",
        values
    )