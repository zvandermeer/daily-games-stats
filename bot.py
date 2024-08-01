import discord
import requests
import os
import datetime

import sheets_connector

intents = discord.Intents.default()
intents.message_content = True

# Load whether to update google sheet or send scores to REST server
updateSheet = os.environ["UPDATE_SHEET"].lower() == "true"
updateServer = os.environ["UPDATE_SERVER"].lower() == "true"

client = discord.Client(intents=intents)

# Start dates for various games to allow for date calculation
connectionStartDate = datetime.datetime(2023, 6, 12)
wordleStartDate = datetime.datetime(2021,6, 20)
waffleStartDate = datetime.datetime(2022, 1, 22)
deluxeStartDate = datetime.datetime(2022, 5, 30)

connectionsColourMap = {
    "🟨🟨🟨🟨": "yellow",
    "🟩🟩🟩🟩": "green",
    "🟦🟦🟦🟦": "blue",
    "🟪🟪🟪🟪": "purple"
}

# Notice the bot is online
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# Every time a message is sent, process the score
@client.event
async def on_message(message):
    if message.channel.name == "daily-games":
        # If sending to a REST server, send the raw data and allow the server to process as it wishes
        if updateServer:
            sendData = {}

            sendData["key"] = os.environ["SERVER_API_KEY"]

            sendData["user"] = message.author.id

            if len(message.attachments) == 1:
                sendData["message"] = message.attachments[0].url
            else:
                sendData["message"] = message.content

            print(sendData)

            requests.post(os.environ["SERVER_ENDPOINT"], data=sendData)
        
        # If sending to a google sheet, processing must be done locally
        if updateSheet:

            # Determine if the player is me or my partner, and update variable accordingly
            player = 0

            if os.environ["MY_DISCORD_ID"] == str(message.author.id):
                player = 1

            # Process message depending on game
            match message.content:
                case s if s.startswith("Connections"):
                    connectionsList = s.split("\n")

                    # Manipulate the message string to isolate the puzzle number, and get
                    # the date from there
                    puzzleNumber = int(connectionsList[1].split("#")[1].replace(",",  ""))
                    puzzleDate = connectionStartDate + datetime.timedelta(days=(puzzleNumber-1))

                    connectionsList = connectionsList[2:]

                    # Get the total number of guesses from the length of the string
                    guesses = len(connectionsList)

                    # Populate position dictionary
                    positions = {
                        "yellow": "-",
                        "green": "-",
                        "blue": "-",
                        "purple": "-"
                    }

                    counter = 1

                    # Get order of successful guesses
                    for row in connectionsList:
                        if row in connectionsColourMap:
                            colour = connectionsColourMap[row]
                            positions[colour] = str(counter)

                            counter += 1

                    # Create row to insert into spreadsheet
                    scoreRow = [[guesses, positions["yellow"], positions["green"], positions["blue"], positions["purple"], "Worked together"]]
                        
                    # Process extracted score data
                    sheets_connector.update_score(sheets_connector.Game.CONNECTIONS, scoreRow, player, puzzleDate)


                case s if s.startswith("Wordle"):
                    wordleList = s.split(" ")

                    # Manipulate the string to isolate the score
                    score = wordleList[2][0]

                    # Manipulate the message string to isolate the puzzle number, and get
                    # the date from there
                    puzzleNumber = int(wordleList[1].replace(",", ""))
                    puzzleDate = wordleStartDate + datetime.timedelta(days=(puzzleNumber-1))

                    # Create row to insert into spreadsheet
                    scoreRow = [[score, "N"]]

                    # Process extracted score data
                    sheets_connector.update_score(sheets_connector.Game.WORDLE, scoreRow, player, puzzleDate)

                    
                case s if s.startswith("https://www.nytimes.com/badges/games/mini.html"):
                    urlData = s.split("&")

                    # Manipulate the string to isolate the score
                    score = urlData[1].split("=")[1]

                    # Obtain the date of the puzzle from the message
                    dateData = urlData[0].split("=")[1].split("-")
                    crosswordStartDate = datetime.datetime(int(dateData[0]), int(dateData[1]), int(dateData[2]))

                    # Create row to insert into spreadsheet
                    scoreRow = [[f"=time(0,0,{score})", "N"]]

                    # Process extracted score data
                    sheets_connector.update_score(sheets_connector.Game.MINI, scoreRow, player, crosswordStartDate)


                case s if s.startswith("#waffle"):
                    waffleList = s.split(" ")

                    # Manipulate the string to isolate the score
                    score = waffleList[1][0]

                    # Manipulate the message string to isolate the puzzle number, and get
                    # the date from there
                    puzzleNumber = int(waffleList[0].split("waffle")[1])
                    puzzleDate = waffleStartDate + datetime.timedelta(days=(puzzleNumber-1))

                    # Create row to insert into spreadsheet
                    scoreRow = [[score, "N"]]

                    # Process extracted score data
                    sheets_connector.update_score(sheets_connector.Game.WAFFLE, scoreRow, player, puzzleDate)


                case s if s.startswith("#deluxewaffle"):
                    waffleList = s.split(" ")

                    # Manipulate the string to isolate the score
                    score = waffleList[1][0]

                    # If the puzzle was failed, obtain the final number of swaps required to 
                    # solve the puzzle
                    if score == "X":
                        swaps = waffleList[2].split("\n")[0].replace("(", "").replace(")", "")
                    else:
                        # If the puzzle was not failed, the number of swaps is 25 - the number of stars
                        swaps = 25 - int(score)

                    # Manipulate the message string to isolate the puzzle number, and get
                    # the date from there
                    puzzleNumber = int(waffleList[0].split("waffle")[1])
                    puzzleDate = deluxeStartDate + datetime.timedelta(days=((puzzleNumber-1)*7))

                    # Create row to insert into spreadsheet
                    scoreRow = [[score, swaps]]

                    # Process extracted score data
                    sheets_connector.update_score(sheets_connector.Game.DELUXE, scoreRow, player, puzzleDate)


                case s if s.startswith("I played https://squaredle.com"):
                    squaredleList = s.split("\n")

                    # Obtain the date of the puzzle from the message
                    now = datetime.datetime.now()
                    dateData = squaredleList[0].split(" ")[3].split("/")
                    puzzleDate = datetime.datetime(now.year, int(dateData[0]), int(dateData[1].replace(":", "")))

                    # If the player scored any bonus words, track it
                    try:
                        bonusWords = squaredleList[1].split("+")[1].split(" ")[0]
                    except IndexError:
                        bonusWords = "0"

                    # If the player has any extra score message, track it
                    try:
                        extraScore = squaredleList[2]
                    except IndexError:
                        extraScore = ""

                    # In the big squaredle, if an extra score message is not present, the
                    # players streak will be found on the same line. If the extra score
                    # is found to be the streak, set it to none
                    if extraScore.startswith("🔥"):
                        extraScore = ""

                    # Determine if the game is the mini squaredle or the big squaredle
                    if squaredleList[0].split(" ")[2].endswith("/xp"):
                        game = sheets_connector.Game.MINI_SQUAREDLE
                    else:
                        game = sheets_connector.Game.BIG_SQUAREDLE

                    # Create row to insert into spreadsheet
                    scoreRow = [[bonusWords, extraScore]]

                    # Process extracted score data
                    sheets_connector.update_score(game, scoreRow, player, puzzleDate)


client.run(os.environ["DISCORD_TOKEN"])