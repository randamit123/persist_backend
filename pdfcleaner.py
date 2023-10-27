import os
from pdfminer.high_level import extract_text
from tqdm import tqdm


class PDFCleaner:
    def __init__(self, school_name="UCI"):
        self.school_name = school_name
        self.output_file = "output.txt"

    def extract_text(self):
        pdf_directory = f"agreements/{self.school_name}"

        if not os.path.exists(pdf_directory):
            print(f"Directory '{pdf_directory}' does not exist.")
            return

        extracted_text_list = []

        pdf_files = [filename for filename in os.listdir(
            pdf_directory) if filename.endswith(".pdf")]

        print("Extracting text from PDFs:")
        with tqdm(total=len(pdf_files), unit="PDF") as pbar:
            for filename in pdf_files:
                pdf_path = os.path.join(pdf_directory, filename)
                try:
                    text = extract_text(pdf_path)
                    extracted_text_list.append(text)
                except Exception as e:
                    print(f"Error extracting text from '{pdf_path}': {str(e)}")
                pbar.update(1)

        with open(self.output_file, "w", encoding="utf-8") as output_file:
            output_file.write("\n\n".join(extracted_text_list))

        print(
            f"Text extracted from {len(extracted_text_list)} PDF files and saved to '{self.output_file}'.")
