## AI History Explored

This is a simple project that explores creation of historic images over time. The goal is to post one historic image every day based on what the LLM sees as the most significant event in history from that particular day.

The results are posted to X and the prompt is posted to pastebin, pastebin is used to document the prompt because the character limits.

## Setup

Set of API keys in environemt variables for x.com, pastebin and OpenAI, best stored in `.env` file.

```
consumer_key=
consumer_secret=
access_token=
access_token_secret=
bearer_token=

OPENAI_API_KEY=

PASTEBIN_API_KEY=
```

There needs to be a `./images/` folder to store the images.

## Prompts

There are three LLM prompts:
1. Creation of the image generation prompt
2. Creation of the image via DALLE using the prompt from (1)
3. Creation of a summary for the tweet

The prompts are hard coded. 

## crontab

Quick solution to run it once a day:

```
sudo crontab -e
```

Add the follwoing line to run every day at 8 in the morning, replace *hacker* with the correct user
```
#*/5 * * * * su - hacker -c 'cd /home/hacker/projects/ai_explored_bot/ && /usr/bin/python3 ai_explored.py'
```
