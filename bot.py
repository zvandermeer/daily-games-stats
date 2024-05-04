import discord
import requests
import os

import sheets_connector

intents = discord.Intents.default()
intents.message_content = True

updateSheet = os.environ["UPDATE_SHEET"] == "True"
updateServer = os.environ["UPDATE_SERVER"] == "True"

client = discord.Client(intents=intents)

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
                        
                    
                    sheets_connector.update_connections(guesses, order, player)

                case s if s.startswith("Wordle"):
                    score = s.split(" ")[2][0]

                    sheets_connector.update_score(sheets_connector.Game.WORDLE, score, player)
                    
                case s if s.startswith("https://www.nytimes.com/badges/games/mini.html"):
                    score = s.split("&")[1].split("=")[1]

                    sheets_connector.update_score(sheets_connector.Game.MINI, f"=time(0,0,{score})", player)

                case s if s.startswith("#waffle"):
                    score = s.split(" ")[1][0]

                    sheets_connector.update_score(sheets_connector.Game.WAFFLE, score, player)

client.run(os.environ["DISCORD_TOKEN"])