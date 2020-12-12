import argparse
import asyncio
import os
import requests
import uuid
import azure.cognitiveservices.speech as speechsdk
from azure.eventhub import EventHubProducerClient, EventData
from azure.eventhub.aio import EventHubConsumerClient
from dotenv import load_dotenv

# Load the keys from the .env file
load_dotenv()
speech_key = os.environ['SPEECH_KEY']
translator_key = os.environ['TRANSLATOR_KEY']
translator_endpoint = os.environ['TRANSLATOR_ENDPOINT']
service_location = os.environ['LOCATION']
event_hub_connection_string = os.environ['EVENT_HUB_CONNECTION_STRING']
event_hub_name = os.environ['EVENT_HUB_NAME']

# Create a sender ID so that we ignore events sent by this instance of the app
sender_id = str(uuid.uuid1())

# Initialize the argument parser
parser = argparse.ArgumentParser()
 
# Add the arguments
# -l/--language - the language this user is speaking in
# -hs/--headset - we don't want the spoken output detected by the input, so by default listening is disabled when there is output.
#   Set this to say you are using a headset so the mic won't detect the voice so we can leave recognition turned on
parser.add_argument("-l", "--language", type=str, help = "The input/output language for this side of the translator", required=True)
parser.add_argument("-hs", "--headset", action='store_true', help = "Pass this if you are using a headset so the spoken voice won't be detected by the mic and translated again")
 
# Read arguments from command line
args = parser.parse_args()

print("Users language is", args.language)
print("Using headset is", args.headset)

# Create an instance of a speech config with specified subscription key and service region.
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_location)
speech_config.speech_recognition_language = args.language
speech_config.speech_synthesis_language = args.language

# Creates a speech recognizer and synthesizer using the default speaker as audio output.
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

# Create an event hub producer and consumer to send and received the text to translate
producer = EventHubProducerClient.from_connection_string(
    conn_str=event_hub_connection_string,
    eventhub_name=event_hub_name
)

consumer_client = EventHubConsumerClient.from_connection_string(
    conn_str=event_hub_connection_string,
    consumer_group='$Default',
    eventhub_name=event_hub_name,
)

# Send text to the event hub
def send_text(speech_text):
    print("Sending:", speech_text)

    # Create an event
    event_data_batch = producer.create_batch()

    # Set the spoken text as the event data
    event_data = EventData(speech_text)

    # Add properties for the sender and the senders language
    event_data.properties = {'sender': sender_id, 'language': args.language}

    # Send the event data as a single entry in a batch
    event_data_batch.add(event_data)
    producer.send_batch(event_data_batch)
    print("sent")

# When a sentence is recognized, send it to event hub
def recognized(args):
    if args.result.text.strip():
        send_text(args.result.text)

# Wire up the recognized event and start listening
speech_recognizer.recognized.connect(recognized)
speech_recognizer.start_continuous_recognition_async()

async def main():
    # Translate the given text to the users language and speak it
    def translate(text, source_language):
        # Build a REST request
        path = '/translate?api-version=3.0'
        params = '&to=' + args.language + '&from=' + source_language
        constructed_url = translator_endpoint + path + params

        # Set the headers
        headers = {
            'Ocp-Apim-Subscription-Key': translator_key,
            'Ocp-Apim-Subscription-Region': service_location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        # Set the body to be translated
        body = [{
            'text' : text
        }]

        # Make the translation REST request
        request = requests.post(constructed_url, headers=headers, json=body)
        response = request.json()

        # Get back the result
        translated = response[0]['translations'][0]['text']

        if not args.headset:
            speech_recognizer.stop_continuous_recognition_async()

        speech_synthesizer.speak_text(translated)

        if not args.headset:
            speech_recognizer.start_continuous_recognition_async()

    async def receive_text(partition_context, event):
        if event.properties[b'sender'].decode('ascii') == sender_id:
            print("Ignoring event")
        else:
            received_language = event.properties[b'language'].decode('ascii')
            received_text = event.body_as_str(encoding='UTF-8')
            print("received", received_text, "in", received_language)
            translate(received_text, received_language)

        await partition_context.update_checkpoint(event)

    async def listen_for_events():
        await consumer_client.receive(on_event=receive_text)

    async def main_loop():
        print("Say something!")
        # Loop forever processing speech
        while True:
            await asyncio.sleep(1)
    
    listeners = asyncio.gather(listen_for_events())

    await main_loop()

    listeners.cancel()

if __name__ == '__main__':
    asyncio.run(main())