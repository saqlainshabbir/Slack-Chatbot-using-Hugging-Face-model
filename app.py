import os
import logging
from dotenv import load_dotenv
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Load environment variables
load_dotenv()

# Get required tokens and API endpoint
HF_TOKEN = os.environ.get("HF_TOKEN")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

	
# Function to query the Huggingface API
def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        # Check for empty response
        if not response.content:
            logging.error("Huggingface API returned an empty response.")
            return None

        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying Huggingface API: {e}")
        return None

# Create Slack app instance
app = App(token=SLACK_BOT_TOKEN)

# Corrected handler for message actions (using @app.shortcut)
@app.shortcut("summarizer-text")
def handle_shortcuts(ack, body, logger, client):
    try:
        ack()
        logger.info(body)  # Process the message action data here

        # Your existing code here...
        message = body["trigger_id"]
        output = query({"inputs": message})
        if output:
            summary = output[0].get("summary_text")
            client.views_open(
                trigger_id=message,
                view={
                    "type": "modal",
                    "callback_id": "summary_modal",
                    "title": {"type": "plain_text", "text": "Summary"},
                    "blocks": [
                        {
                            "type": "section",
                            "block_id": "summary_block",
                            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"},
                        }
                    ],
                },
            )
    except Exception as e:
        logging.error(f"Error handling shortcut: {e}")

# Handle message events (changed to @app.event)
@app.event("message")
def handle_message_events(body, logger, client):
    logger.info(body)
    try:
        message_text = body.get("event", {}).get("text", "")
        logger.debug(message_text)
        if message_text:
            output = query({"inputs": message_text})
            if output:
                summary = output[0].get("summary_text")
                
                client.chat_postEphemeral(
                    channel=body["event"]["channel"],
                    user=body["event"]["user"],
                    text="Here is your summary",
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": summary}}],
                )
    except Exception as e:
        logging.error(f"Error handling message: {e}")

# Handle app home opened events (added @app.event decorator)
@app.event("app_home_opened")
def handle_app_home_opened_events(body, logger):
    logger.info(body)

# Start the app in Socket Mode
if __name__ == "__main__":
    SocketModeHandler(app, app_token=SLACK_APP_TOKEN).start()