from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import filedialog
from azure.core.exceptions import HttpResponseError
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential


def main():
    global cv_client

    try:
        # Get Configuration Settings
        load_dotenv()
        ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
        ai_key = os.getenv('AI_SERVICE_KEY')

        # Open file dialog to select an image
        root = tk.Tk()
        root.withdraw()  # Hide the main tkinter window
        image_file = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")]
        )

        if not image_file:
            print("No image selected.")
            return

        with open(image_file, "rb") as f:
            image_data = f.read()

        # Authenticate Azure AI Vision client
        cv_client = ImageAnalysisClient(
            endpoint=ai_endpoint,
            credential=AzureKeyCredential(ai_key)
        )

        # Analyze image
        AnalyzeImage(image_file, image_data, cv_client)

    except Exception as ex:
        print(f"Error: {ex}")


def AnalyzeImage(image_filename, image_data, cv_client):
    try:
        # Get result with specified features to be retrieved
        result = cv_client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.CAPTION]
        )
    except HttpResponseError as e:
        print(f"Error: {e.error.message}")
        return

    # Display the description of the image
    if result.caption is not None:
        print(result.caption.text)


if __name__ == "__main__":
    main()
