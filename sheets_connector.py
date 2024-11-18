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
    MINI_SQUAREDLE = 'U'
    BIG_SQUAREDLE = 'W'
    ZORSE = 'Z'

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
    
def update_score(game, rowData, player, puzzleDate):
    # Find the row to update
    row = find_row(puzzleDate)

    # Find number of columns required to update
    columns = len(rowData[0])

    # Update the values on the sheet
    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{game}{row+player}:{chr(ord(game)+columns)}{row+player}",
        "USER_ENTERED",
        rowData
    )

def update_zorse(player, question, score, puzzleDate):
    row = find_row(puzzleDate)

    # Update question
    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{Game.ZORSE}{row}:{Game.ZORSE}{row}",
        "USER_ENTERED",
        [[question]]
    )

    # Update score
    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!AA:AA{row+player}",
        "USER_ENTERED",
        [[score]]
    )
