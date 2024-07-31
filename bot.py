import discord
import requests
import os
import datetime

import sheets_connector

intents = discord.Intents.default()
intents.message_content = True

updateSheet = os.environ["UPDATE_SHEET"] == "True"
updateServer = os.environ["UPDATE_SERVER"] == "True"

client = discord.Client(intents=intents)

connectionStartDate = datetime.datetime(2023, 6, 12)
wordleStartDate = datetime.datetime(2021,6, 20)
waffleStartDate = datetime.datetime(2022, 1, 21)
deluxeStartDate = datetime.datetime(2022, 5, 29)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.name == "daily-games":
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
        
        if updateSheet:
            player = 0

            if os.environ["MY_DISCORD_ID"] == str(message.author.id):
                player = 1

            match message.content:
                case s if s.startswith("Connections"):
                    connectionsList = s.split("\n")

                    order = []

                    puzzleNumber = int(connectionsList[1].split("#")[1].replace(",",  ""))
                    puzzleDate = connectionStartDate + datetime.timedelta(days=(puzzleNumber-1))

                    guesses = len(connectionsList) - 2

                    for i in connectionsList:
                        match i:
                            case "🟨🟨🟨🟨":
                                order.append("yellow")
                            case "🟩🟩🟩🟩":
                                order.append("green")
                            case "🟦🟦🟦🟦":
                                order.append("blue")
                            case "🟪🟪🟪🟪":
                                order.append("purple")
                        
                    
                    sheets_connector.update_connections(guesses, order, player, puzzleDate)

                case s if s.startswith("Wordle"):
                    wordleList = s.split(" ")
                    score = wordleList[2][0]
                    puzzleNumber = int(wordleList[1].replace(",", ""))

                    puzzleDate = wordleStartDate + datetime.timedelta(days=(puzzleNumber-1))

                    sheets_connector.update_score(sheets_connector.Game.WORDLE, score, player, puzzleDate)
                    
                case s if s.startswith("https://www.nytimes.com/badges/games/mini.html"):
                    urlData = s.split("&")
                    score = urlData[1].split("=")[1]

                    dateData = urlData[0].split("=")[1].split("-")

                    crosswordStartDate = datetime.datetime(int(dateData[0]), int(dateData[1]), int(dateData[2]))

                    sheets_connector.update_score(sheets_connector.Game.MINI, f"=time(0,0,{score})", player, crosswordStartDate)

                case s if s.startswith("#waffle"):
                    waffleList = s.split(" ")
                    score = waffleList[1][0]

                    puzzleNumber = int(waffleList[0].split("waffle")[1])

                    puzzleDate = waffleStartDate + datetime.timedelta(days=(puzzleNumber-1))

                    sheets_connector.update_score(sheets_connector.Game.WAFFLE, score, player, puzzleDate)

                case s if s.startswith("#deluxewaffle"):
                    waffleList = s.split(" ")
                    score = waffleList[1][0]

                    if score == "X":
                        swaps = waffleList[2].split("\n")[0].replace("(", "").replace(")", "")
                    else:
                        swaps = 25 - int(score)

                    puzzleNumber = int(waffleList[0].split("waffle")[1])

                    puzzleDate = deluxeStartDate + datetime.timedelta(days=((puzzleNumber-1)*7))

                    sheets_connector.update_deluxe(score, swaps, player, puzzleDate)

client.run(os.environ["DISCORD_TOKEN"])