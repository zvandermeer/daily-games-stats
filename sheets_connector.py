import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]

class Game():
    CONNECTIONS = 'C'
    WORDLE = 'J'
    MINI = 'M'
    WAFFLE = 'P'
    DELUXE = 'R'
    MINI_SQUARDLE = 'U'
    BIG_SQUARDLE = 'W'

def new_day(row, puzzleDate):
    values = [[puzzleDate.strftime("%m/%d/%Y"), "Olivia"], ["", "Zoey"]]

    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!A{row}:B{row+1}",
        "USER_ENTERED",
        values
    )

def find_row(puzzleDate):
    SERVICE_ACCOUNT_FILE = "service_account_credentials.json"
    credentials = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE
    )

    try:
        service = build('sheets', 'v4', credentials=credentials)

        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A:A", valueRenderOption="UNFORMATTED_VALUE")
            .execute()
        )
        values = result.get("values")

        epoch = datetime(1900, 1, 1)

        last_day = epoch + timedelta(days=values[-1][0] - 2)

        delta = (puzzleDate - last_day).days

        if delta == 0:
            return len(values)

        else:
            row = len(values) + (delta * 2)
            new_day(row, puzzleDate)
            return row

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def update_raw_values(spreadsheet_id, range_name, value_input_option, values):
    SERVICE_ACCOUNT_FILE = "service_account_credentials.json"
    credentials = service_account.Credentials.from_service_account_file(
        filename=SERVICE_ACCOUNT_FILE
    )

    try:
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
    collaborate = 'N'

    # if game == Game.MINI:
    #     collaborate = "Worked together"

    values = [[score, collaborate]]

    row = find_row(puzzleDate)

    update_raw_values(
        SPREADSHEET_ID,
        f"{SHEET_NAME}!{game}{row+player}:{chr(ord(game)+1)}{row+player}",
        "USER_ENTERED",
        values
    )

def update_connections(guesses, order, player, puzzleDate):
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

    values = [[guesses, yellowPos, greenPos, bluePos, purplePos, "Worked together"]]

    row = find_row(puzzleDate)

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