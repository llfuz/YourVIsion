from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
from azure.ai.translation.text import *
from azure.ai.translation.text.models import InputTextItem

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION")
TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")

# Create Translator client
credential = TranslatorCredential(TRANSLATOR_KEY, TRANSLATOR_REGION)
client = TextTranslationClient(credential)

# Fetch supported languages
languages_response = client.get_languages(scope="translation")
supported_languages = languages_response.translation  # Dictionary of language codes and names


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get input text and selected language
        input_text = request.form.get("input_text")
        target_language = request.form.get("language_code")

        if not input_text or not target_language:
            return render_template(
                "index.html",
                supported_languages=supported_languages,
                error="Please provide both text and a target language.",
            )

        try:
            # Translate the text
            input_text_elements = [InputTextItem(text=input_text)]
            translation_response = client.translate(content=input_text_elements, to=[target_language])

            if translation_response:
                translation = translation_response[0]
                translated_text = translation.translations[0].text if translation.translations else "Translation failed."
                source_language = translation.detected_language.language

                # Render the result
                return render_template(
                    "index.html",
                    supported_languages=supported_languages,
                    input_text=input_text,
                    target_language=target_language,
                    source_language=source_language,
                    translated_text=translated_text,
                )
            else:
                return render_template(
                    "index.html",
                    supported_languages=supported_languages,
                    error="Translation failed. Please try again.",
                )
        except Exception as e:
            return render_template(
                "index.html",
                supported_languages=supported_languages,
                error=f"An error occurred: {str(e)}",
            )

    # GET request: Render the form
    return render_template("index.html", supported_languages=supported_languages)


if __name__ == "__main__":
    app.run(debug=True)