import os
import logging
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from dotenv import load_dotenv
load_dotenv()


from datadog import DatadogRum
# Initializes your app with your bot token and socket mode handler
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


def _generate_message(urls):
    urls_blocks = [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"• {url} "
        }} for url in urls
    ]
    blocks = [
                 {
                     "type": "section",
                     "text": {
                         "type": "mrkdwn",
                         "text": f"Look, I found some related :dog: sessions:\n"
                     }
                 }] + urls_blocks
    return blocks

# https://slack.dev/bolt-python/concepts#event-listening
@app.event("message")
def handle_message_events(body, logger, say):
    """
    Listen to the message event, parse the context, search for the sessions, and send them to the client

    :param body: https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html#slack_bolt.kwargs_injection.args.Args.body
    :param logger: https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html#slack_bolt.kwargs_injection.args.Args.logger
    :param say: https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html#slack_bolt.kwargs_injection.args.Args.say
    """
    logger.info("Starting to handle event")
    message = body.get("event", {}).get("message")
    if not message:
        logger.info("Skipping message - couldn't parse message", extra={
            "m": message
        })
        return

    ts = message.get('ts')
    attachments = message.get("attachments")
    if not "A conversation started" in attachments[0].get("pretext"):
        logger.info("skipping - no conversation started", extra={
            "m": message
        })
        return

    # extract the email from the fields
    email = attachments[0].get("fields")[3].get("value").split("|")[1][:-1]
    logger.info(f"Handling conversation started by {email}", extra={
        "email": email
    })
    # Now get the sessions
    dd_client = DatadogRum()
    urls = dd_client.get_rum_sessions(email)
    if urls:
        logger.info("Found sessions")
        message = _generate_message(urls)
        say({"blocks": message, "thread_ts": ts})
    else:
        logger.info("Couldn't find sessions")


# Start your app
if __name__ == "__main__":
    print("Starting the slack handlers")
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
