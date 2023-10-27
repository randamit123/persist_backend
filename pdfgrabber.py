import urllib.request
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from PyPDF2 import PdfMerger


class PDFGrabber():
    def __init__(self, school_name='UCSC', school_id=120, major='Game Design & Interactive Media, B.S.', major_code='GDIM', delay=0.5):
        self.school_name = school_name
        self.school_id = school_id
        self.major = major
        self.major_code = major_code
        self.delay = delay

    def get_agreements(self):
        with urllib.request.urlopen(f'https://assist.org/api/institutions/{self.school_id}/agreements') as url:
            data = json.loads(url.read().decode())
        agreement_list = []
        for agreement in list(data):
            if agreement['isCommunityCollege']:
                school_id = agreement['institutionParentId']
                year = agreement['sendingYearIds'][-1]
                curr = {'id': school_id, 'year': year}
                agreement_list.append(curr)
        return agreement_list

    def get_keys(self):
        agreement_list = self.get_agreements()
        keys = []

        key_progress = tqdm(total=len(agreement_list), desc="Collecting Keys")

        def fetch_keys(agreement):
            school_id, year = agreement['id'], agreement['year']
            with urllib.request.urlopen(f'https://assist.org/api/agreements?receivingInstitutionId={self.school_id}&sendingInstitutionId={school_id}&academicYearId={year}&categoryCode=major') as url:
                data = json.loads(url.read().decode())
            data = data['reports']
            for report in list(data):
                if report['label'] == self.major:
                    keys.append({'key': report['key'], 'school_id': school_id})
                    key_progress.update(1)

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_keys, agreement)
                       for agreement in agreement_list]

        for future in as_completed(futures):
            future.result()

        key_progress.close()
        print("Keys collected")

        return keys

    def get_pdfs(self):
        keys = self.get_keys()
        id_to_key = {}
        save_directory = f'agreements/{self.school_name}'

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        def download_pdf(key, school_id):
            key_val = key
            if key_val is not None:
                pdf_url = f'https://assist.org/api/artifacts/{key_val}'
                file_name = f'{save_directory}/report_{self.school_id}_{school_id}_{self.major_code}.pdf'
                try:
                    with open(file_name, 'wb') as f:
                        f.write(urllib.request.urlopen(pdf_url).read())
                    id_to_key[school_id] = key_val
                except Exception as e:
                    print(
                        f"Error while saving PDF for school ID {school_id}: {str(e)}")
            else:
                print("Error key value is null")

        threads = []
        for key in keys:
            school_id = key['school_id']
            key_val = key['key']
            thread = threading.Thread(
                target=download_pdf, args=(key_val, school_id))
            threads.append(thread)
            thread.start()

        pdf_progress = tqdm(total=len(keys), desc="Storing PDFs")

        for thread in threads:
            thread.join()
            pdf_progress.update(1)

        pdf_progress.close()
        print("Agreements stored")
        self.combine_pdfs()

        return id_to_key

    def combine_pdfs(self):
        save_directory = f'agreements/{self.school_name}'

        pdf_merger = PdfMerger()

        for filename in os.listdir(save_directory):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(save_directory, filename)
                pdf_merger.append(pdf_path)

        combined_pdf_path = f'agreements/{self.school_name}/combined_{self.school_name}_agreements.pdf'

        pdf_merger.write(combined_pdf_path)

        pdf_merger.close()

        for filename in os.listdir(save_directory):
            if filename.endswith(".pdf") and 'report' in filename:
                pdf_path = os.path.join(save_directory, filename)
                os.remove(pdf_path)

        print(f"PDF files combined and saved to '{combined_pdf_path}'.")
