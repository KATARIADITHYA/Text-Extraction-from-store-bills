
import io
from PIL import Image
import streamlit as st
from paddleocr import PaddleOCR
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
import pandas as pd
import numpy as np

def fetch_image_from_drive(file_id, drive_service):
    request = drive_service.files().get_media(fileId=file_id)
    file_stream = request.execute()
    image = Image.open(io.BytesIO(file_stream))
    return image

def main():
    # Load the credentials from the JSON key file
    credentials = service_account.Credentials.from_service_account_file('C:/Users/ACER/Desktop/Bills project/imageextraction.json')

    # Build the Google Drive API client
    drive_service = build('drive', 'v3', credentials=credentials)

    # Get folder ID from user input
    folder_id = st.text_input('Enter the folder ID:')

    if folder_id:
        # List all the image files in the folder
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'image/'",
            fields="files(id, name)").execute()
        files = results.get('files', [])
        
        ocr = PaddleOCR()
        data = []

        for file in files:
            image = fetch_image_from_drive(file['id'], drive_service)
            image_array = np.array(image)
            result = ocr.ocr(image_array)
            text = "\n".join(row[1][0] for row in result[0])

            st.write("Extracted Text:")
            st.write(text)

            billpattern = r"\d{9}-\d{6}"
            datepattern = r"\d{2}\/\d{2}\/\d{4}"
            billmatch = re.findall(billpattern, text)
            if billmatch:
                billnumber = billmatch[0]
            else:
                billnumber = 'Not found'

            datematch = re.findall(datepattern, text)
            if datematch:
                date = datematch[0]
            else:
                date = 'Not found'

            pattern = r"\d+\s*[A-Za-z\s-]+\d+(?:\.\d+)?[A-Za-z]+(?:\.\d+)?\s+\d+(?:\.\d+)?\s+\d+(?:\.\d+)?"
            matches = re.findall(pattern, text)

            for match in matches:
                parts = match.split('\n')
                product_name = parts[0]
                if '.' in parts[1]:
                    quantity = ""
                    price = parts[1]
                else:
                    quantity = parts[1]
                    price = parts[2]
                data.append([billnumber, date, product_name, quantity, price])

        df = pd.DataFrame(data, columns=['Bill number', 'Date', 'Product Name', 'Quantity', 'Price'])

        st.write("Extracted Data:")
        st.write(df)

if __name__ == '__main__':
    main()
