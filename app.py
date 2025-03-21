import os
import PyPDF2
from openai import OpenAI

client = OpenAI()
import json
import os
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil

PROMPT = """
Your are an assistant that helps the user to analyze documents and categorizes them.
In case the document is an invoice or a credit note, extract the vendor and the date and return a JSON structure according to this format:

{
"type":"invoice",
"vendor":"LinkedIn",
"date":"2024-03-23"

}

In case "David Schuld IT Consulting AB" is written on the document, do not use this as the vendor. So an invoice that contains "David Schuld IT Consulting AB" should have as the vendor the other company that is mentioned on the invoice.
In case the document is not an invoice or a credit note, return this structure:

{
"type":"other"
}

Only return the JSON. Do not output any additional text. Do not enclose the JOSN in tags like "```json()" or something like that. Only output valid JSON.

This is the document in text form:

"""

DOWNLOADS_DIR = "/mnt/Downloads"
PROCESSED_DIR = "/mnt/processed"

def read_pdf_file(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
            
    return text

def call_gpt(text):
    messages = [{"role": "user", "content": text}]
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=messages)
    response_message = response.choices[0].message.content    
    data_structure = json.loads(response_message)
    return data_structure


def move_and_rename_file(source_path, destination_folder, new_filename):
    filename = os.path.basename(source_path)
    destination_path = os.path.join(destination_folder, new_filename)
    shutil.move(source_path, destination_path)
    print(f"File '{filename}' moved and renamed to '{new_filename}' in '{destination_folder}'.")



def process_file(path, metadata):
    print("Received metadata: " + json.dumps(metadata))
    if (metadata["type"] == "invoice" or metadata["type"] == "credit_note" or metadata["type"] == "credit note"):
        print("Moving file to invoices")
        new_filename = metadata["vendor"] + "-" + metadata["date"] + ".pdf"
        move_and_rename_file(path, PROCESSED_DIR, new_filename)
    else:
        print("No invoice - leaving file in Downloads folder")



class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.pdf'):
            file_size = os.path.getsize(event.src_path)
            if file_size < 200 * 1024: 
                text = read_pdf_file(event.src_path)
                process_file(event.src_path, call_gpt(PROMPT + text))
            else:
                print(f"File '{event.src_path}' is larger than 200 KB and will not be processed.")



def monitor_downloads_folder(path):
    event_handler = PDFHandler()
    print(f"Monitoring folder '{path}' for new PDF files...")
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Monitoring stopped")

# Example usage
monitor_downloads_folder(DOWNLOADS_DIR)


