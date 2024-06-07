import tweepy
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import utils

# Load environment variables
load_dotenv()
consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')
bearer_token = os.getenv('bearer_token')
pastebin_api_key = os.getenv('PASTEBIN_API_KEY')

oai_client = OpenAI()
x_client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

log_file = 'details.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

if __name__ == '__main__':
    todays_date = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"***** Starting image generation for {todays_date}")

    attempts = 0
    max_attempts = 3
    success = False
    summary = ""
    image_prompt = ""

    while attempts < max_attempts and not success:
        try:
            image_prompt = utils.get_image_generation_prompt(todays_date)
            logging.info(f"The prompt for today is: {image_prompt}. Length: {len(image_prompt)}")

            image_url = utils.generate_image_with_dalle(image_prompt)
            image_path = f"./images/historic-{todays_date}.png"
            unique_image_path = utils.get_unique_filename(image_path)
            utils.download_image(image_url, unique_image_path)

            success = True
        except Exception as e:
            if "content_policy_violation" in str(e):
                logging.warning(f"Content policy violation error encountered. Retrying... Attempt {attempts + 1}")
                attempts += 1
            else:
                logging.error(f"An unexpected error occurred: {e}")
                exit()
                break

    if not success:
        logging.error("Failed to generate image after n attempts due to content policy violations.")
        exit()

    if unique_image_path == image_path:
        try:
            summary = utils.get_summary(image_prompt)
            summary += " #ai_explored"
            logging.info(f"Generated summary of prompt... {summary}")
            initial_tweet_id = utils.post_image(x_client, summary, unique_image_path)

            if initial_tweet_id:
                paste_name = f"AI history prompt for {todays_date} (https://x.com/ai_explored)"
                success, url = utils.create_paste(pastebin_api_key, paste_name, image_prompt)
                logging.info(f"Prompt posted to pastebin: {url}")
                subtweet = f"The auto-generated prompt for today can be found here: {url}"
                tweets = utils.split_text_into_tweets(subtweet)
                utils.post_tweets(x_client, tweets, initial_tweet_id)
                logging.info("Tweets posted successfully.")
            else:
                logging.error("Failed to post initial image tweet.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while downloading or posting the image: {e}")
    else:
        logging.error("An image already existed for today, hence not posting.")

    logging.info(f"***** Done for {todays_date}.")
