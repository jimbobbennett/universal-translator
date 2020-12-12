# Universal translator

A universal translator allowing folks in different countries to speak to each other in different languages.

This Python app uses the [Azure Cognitive Services Speech service](https://azure.microsoft.com/services/cognitive-services/speech-services/?WT.mc_id=cademic-11379-jabenn) to listen for speech in a given language. When speech is detected, it is sent over an [Azure event hub](https://azure.microsoft.com/services/event-hubs/?WT.mc_id=cademic-11379-jabenn). Another instance of this app listens on the event hub and when a message is received, it is translated to a given language using the [Microsoft Cognitive Services translator service](https://azure.microsoft.com/services/cognitive-services/translator/?WT.mc_id=cademic-11379-jabenn). It is then converted to speech using the speech service and spoken out loud.

To use this example:

* Create a Cognitive services speech resource and translator service resource

* Create an event hubs namespace and an event hub

* Create a `.env` file with the following:

    ```sh
    SPEECH_KEY=
    SPEECH_LOCATION=
    TRANSLATOR_KEY=
    TRANSLATOR_LOCATION=
    TRANSLATOR_ENDPOINT=
    EVENT_HUB_CONNECTION_STRING=
    EVENT_HUB_NAME=
    ```

    Fill in the values using your speech service key and location, translation service key, location and end point, and event hub connection string and hub name. This connection string needs send and receive permissions.

* Create a Python virtual environment and install the pip packages from the `requirements.txt` file

* Run the `universal-translator.py` file passing in the following arguments:

    -l/--language - the language you are using. See the [supported languages documentation](https://docs.microsoft.com/azure/cognitive-services/speech-service/language-support?WT.mc_id=cademic-11379-jabenn) for a list of languages.

    -hs/--headset - pass this if you are using a headset. Recognition is turned off when speaking to avoid sending the output back, this stops the recognition turn off if you are wearing a headset so the mic can't pick up the output