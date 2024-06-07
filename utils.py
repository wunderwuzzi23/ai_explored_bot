import tweepy
from openai import OpenAI
import os
import requests
import logging

def post_tweet(client, message, in_reply_to_tweet_id=None):
    """Post a tweet using Twitter API v2"""
    try:
        response = client.create_tweet(text=message, in_reply_to_tweet_id=in_reply_to_tweet_id)
        logging.info(f"Tweet posted successfully: {response.data}")
        return response.data['id']
    except tweepy.TweepyException as e:
        logging.error(f"Error: {e}")
        return None

def post_image(client, message, image_path):
    """Post a tweet with an image using Twitter API v1.1 for media upload and API v2 for tweeting"""
    auth = tweepy.OAuth1UserHandler(
        consumer_key=os.getenv('consumer_key'),
        consumer_secret=os.getenv('consumer_secret'),
        access_token=os.getenv('access_token'),
        access_token_secret=os.getenv('access_token_secret')
    )
    api = tweepy.API(auth)
    try:
        media = api.media_upload(image_path)
        response = client.create_tweet(text=message, media_ids=[media.media_id])
        logging.info(f"Tweet with image posted successfully: {response.data}")
        return response.data['id']
    except tweepy.TweepyException as e:
        logging.error(f"Error: {e}")
        return None

def get_image_generation_prompt(todays_date):
    system_prompt = f"Today is {todays_date}, the date format is YYYY-MM-dd. You are a historian and concise AI prompting expert for DALLE-3."
    prompt = f"""Create an image generation prompt for the most significant historical event for precisely and only today's date: {todays_date}. 
Research details and significance the event, and ensure the year of the event is clearly visible in the image. 
Make it epic, be historically accurate."""

    oai_client = OpenAI()
    response = oai_client.chat.completions.create(model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=512,
        temperature=1
    )
    
    response = response.choices[0].message.content
    return response

def get_summary(text):
    system_prompt = f"""Summarize the following text for a short concise tweet (max 180 characters), use emojis. 
Be neutral and objective in the summary. Do not use words like epic or vivid, focus to highlight day and event. 
Conclude by mentioning that the prompt for the image and the image are AI auto-generated."""
    prompt = f"""Text: {text}"""

    oai_client = OpenAI()
    response = oai_client.chat.completions.create(model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.6
    )
    
    response = response.choices[0].message.content
    return response

def generate_image_with_dalle(image_prompt):
    oai_client = OpenAI()
    response = oai_client.images.generate(
        prompt=image_prompt,
        model="dall-e-3",
        n=1,
        size="1024x1024"
    )
    
    return response.data[0].url

def get_unique_filename(base_path):
    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(base_path)
    counter = 1
    unique_path = f"{name}_{counter}{ext}"
    
    while os.path.exists(unique_path):
        counter += 1
        unique_path = f"{name}_{counter}{ext}"
    
    return unique_path

def download_image(image_url, local_filename):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(local_filename, 'wb') as file:
            file.write(response.content)
        logging.info(f"Image downloaded successfully: {local_filename}")
    else:
        logging.error(f"Failed to download image. Status code: {response.status_code}")

def split_text_into_tweets(text, max_length=280):
    """Splits text into tweet-sized chunks, ensuring splits occur only at spaces."""
    words = text.split()
    tweets = []
    current_tweet = ""

    for word in words:
        if len(current_tweet) + len(word) + 1 <= max_length:
            current_tweet += " " + word if current_tweet else word
        else:
            tweets.append(current_tweet)
            current_tweet = word

    if current_tweet:
        tweets.append(current_tweet)
    
    return tweets

def post_tweets(client, tweets, initial_tweet_id):
    """Post a sequence of tweets as a thread, starting from the initial tweet ID."""
    try:
        previous_tweet_id = initial_tweet_id
        for tweet in tweets:
            response = client.create_tweet(text=tweet, in_reply_to_tweet_id=previous_tweet_id)
            previous_tweet_id = response.data['id']
            logging.info(f"Tweet posted successfully: {response.data}")
    except tweepy.TweepyException as e:
        logging.error(f"Error: {e}")

def create_paste(api_key, paste_name, image_prompt):
    """
    Create a paste on Pastebin.

    Parameters:
    - api_key (str): Your Pastebin API key.
    - image_prompt (str): The content to be posted.

    Returns:
    - str: URL of the created paste if successful, error message otherwise.
    """
    url = "https://pastebin.com/api/api_post.php"
    payload = {
        'api_dev_key': api_key,
        'api_option': 'paste',
        'api_paste_code': image_prompt,
        'api_paste_name': paste_name,
        'api_paste_expire_date': 'N',
        'api_paste_format': 'text',
        'api_paste_private': '0',  # 0 = public, 1 = unlisted, 2 = private
        'api_paste_tag': 'ai_explored',
        'api_paste_category': 'history'
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        return True, f"{response.text}"
    else:
        return False, f"ERROR. Status code: {response.status_code}, Response: {response.text}"
