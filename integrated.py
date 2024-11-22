from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import filedialog
from azure.core.exceptions import HttpResponseError
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient, TranslatorCredential
from azure.ai.translation.text.models import InputTextItem
import azure.cognitiveservices.speech as speechsdk


def main():
    # Load environment variables
    load_dotenv()

    # Vision API configuration
    ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
    ai_key = os.getenv('AI_SERVICE_KEY')

    # Translator API configuration
    translatorRegion = os.getenv('TRANSLATOR_REGION')
    translatorKey = os.getenv('TRANSLATOR_KEY')

    # Speech API configuration
    speech_key = os.getenv('SPEECH_KEY')
    service_region = os.getenv('SPEECH_REGION')

    # Select an image
    root = tk.Tk()
    root.withdraw()
    image_file = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")]
    )
    if not image_file:
        print("No image selected.")
        return

    with open(image_file, "rb") as f:
        image_data = f.read()

    # Authenticate Vision API client
    vision_client = ImageAnalysisClient(
        endpoint=ai_endpoint,
        credential=AzureKeyCredential(ai_key)
    )

    # Analyze the image to get a caption
    print("Analyzing the image...")
    caption_text = analyze_image(image_data, vision_client)
    if not caption_text:
        print("No caption found.")
        return

    print(f"Image description: {caption_text}")

    # Authenticate Translator API client
    translator_credential = TranslatorCredential(translatorKey, translatorRegion)
    translator_client = TextTranslationClient(translator_credential)

    # Choose target language
    target_language = choose_language(translator_client)

    # Translate the caption
    print("Translating the caption...")
    translated_text = translate_text(caption_text, target_language, translator_client)
    if not translated_text:
        print("Translation failed.")
        return

    print(f"Translated description: {translated_text}")

    # Synthesize speech
    print("Converting text to speech...")
    synthesize_speech(translated_text, speech_key, service_region)


def analyze_image(image_data, vision_client):
    try:
        result = vision_client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.CAPTION] 
        )
        if result.caption:
            return result.caption.text
    except HttpResponseError as e:
        print(f"Error during image analysis: {e.error.message}")
    return None


def choose_language(translator_client):
    languages_response = translator_client.get_languages(scope="translation")
    print(f"{len(languages_response.translation)} languages supported.")
    print("Enter a target language code for translation (e.g., 'en' for English, 'fr' for Franch, 'de' for German):")

    while True:
        target_language = input("Target language: ").strip()
        if target_language in languages_response.translation:
            return target_language
        print(f"{target_language} is not a supported language. Please try again.")


def translate_text(text, target_language, translator_client):
    input_text_elements = [InputTextItem(text=text)]
    translation_response = translator_client.translate(content=input_text_elements, to=[target_language])
    if translation_response and translation_response[0].translations:
        return translation_response[0].translations[0].text
    return None 


def synthesize_speech(text, speech_key, service_region):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized successfully.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")
    except Exception as e:
        print(f"Error during speech synthesis: {e}")


if __name__ == "__main__":
    main()
