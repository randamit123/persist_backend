from pdfgrabber import PDFGrabber
from pdfminer.high_level import extract_text
from pdfcleaner import PDFCleaner
import requests
import re


def get_institutions():
    url = "https://assist.org/api/institutions"
    response = requests.get(url)

    institution_data = {}

    if response.status_code == 200:
        data = response.json()

        for institution in data:
            institution_id = institution["id"]
            names = institution["names"]
            is_community_college = institution["isCommunityCollege"]

            school_name = names[0]["name"]

            institution_data[institution_id] = {
                "School Name": school_name,
                "Is Community College": is_community_college
            }

    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

    return institution_data


def split_institutions_by_type(institution_data):
    community_colleges = {}
    universities = {}

    for institution_id, data in institution_data.items():
        is_community_college = data["Is Community College"]
        if is_community_college:
            community_colleges[institution_id] = data
        else:
            universities[institution_id] = data

    return community_colleges, universities


def print_institutions(institution_data, title):
    print(title)
    for institution_id, data in institution_data.items():
        print(f"ID: {institution_id}, Data: {data}")


def generate_agreement_urls(university_id, community_colleges):
    agreement_urls = []

    for community_id, community_data in community_colleges.items():
        community_school_name = community_data.get("School Name", "Unknown")
        url = f"https://assist.org/api/agreements?receivingInstitutionId={university_id}&sendingInstitutionId={community_id}&academicYearId=73&categoryCode=major"
        agreement_urls.append((community_school_name, url))

    return agreement_urls


def scrape_major_data(agreement_urls):
    major_data_dict = {}

    for school_name, url in agreement_urls:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            reports = data.get("reports", [])

            major_data_list = []

            for report in reports:
                major_data = {
                    "Major Label": report.get("label"),
                    "Major Key": report.get("key"),
                }
                major_data_list.append(major_data)

            major_data_dict[school_name] = major_data_list

        else:
            print(f"Failed to retrieve data from URL: {url}")

    return major_data_dict


def abbreviate_majors(major_label):
    words = major_label.split()

    ignore_words = ["major", "minor", "b.s.", "b.a.", "studies"]

    filtered_words = [word for word in words if word.lower(
    ) not in ignore_words and word.lower() != "and"]

    if len(filtered_words) == 1:
        abbreviated_major = filtered_words[0][:4].upper()
    else:
        abbreviations = []
        abbreviation_counts = {}

        for word in filtered_words:
            match = re.match(r'\(([^)]+)\)', word)
            if match:
                abbreviated_word = match.group(1)[0].upper()
            else:
                abbreviated_word = word[0].upper()

            if abbreviated_word in abbreviation_counts:
                abbreviation_counts[abbreviated_word] += 1
                abbreviated_word = f"{abbreviated_word}{abbreviation_counts[abbreviated_word]}"
            else:
                abbreviation_counts[abbreviated_word] = 1

            abbreviations.append(abbreviated_word)

        abbreviated_major = ''.join(abbreviations)

    return abbreviated_major


def filter_duplicate_majors(major_data_dict):
    unique_majors = []

    seen_majors = set()

    for school_name, majors in major_data_dict.items():
        for major in majors:
            major_label = major['Major Label']
            if major_label not in seen_majors:
                seen_majors.add(major_label)
                unique_majors.append(major_label)

    return unique_majors


def sort_and_print_majors(unique_major_data, unique_major_data_with_abbreviations, school):
    sorted_majors = sorted(
        zip(unique_major_data, unique_major_data_with_abbreviations))

    print(f'\nSchool: {school}')
    print("Length:", len(sorted_majors))
    for major_name, abbreviation in sorted_majors:
        print(major_name, abbreviation)


def main():
    print("Program Start:")

    institution_data = get_institutions()
    community_colleges, universities = split_institutions_by_type(
        institution_data)

    delay = 0.2

    # optimize by multithreading?
    # don't combine every pdf because it

    for school_id, school_data in universities.items():
        school_name = school_data['School Name']

        print(f'School: {school_name}')

        agreement_urls = generate_agreement_urls(school_id, community_colleges)

        print("Agreement URLs found.")

        major_data_dict = scrape_major_data(agreement_urls)

        print("Agreement data colelcted.")

        unique_major_data = filter_duplicate_majors(major_data_dict)

        print("Filtered all unique major agreements.")

        unique_major_data_with_abbreviations = [
            abbreviate_majors(major) for major in unique_major_data]

        print("Created major abbreviations.")

        sort_and_print_majors(
            unique_major_data, unique_major_data_with_abbreviations, school_name)

        for major_label, abbreviated_major in zip(unique_major_data, unique_major_data_with_abbreviations):
            grabber = PDFGrabber(
                school_name, school_id, major_label, abbreviated_major, delay)

            grabber.get_pdfs()

            print(
                f"Major Label: {major_label}, Abbreviated Major: {abbreviated_major}")

    print("Program Ended")


'''
def main():
    print("Program Start:")

    institution_data = get_institutions()
    community_colleges, universities = split_institutions_by_type(
        institution_data)

    sorted_universities = sorted(
        universities.items(), key=lambda item: item[1]["School Name"])
    sorted_universities_dict = {item[0]: item[1]
                                for item in sorted_universities}

    school_id = 132
    school = "UCSC"
    delay = 0.2

    print(sorted_universities_dict)


    agreement_urls = generate_agreement_urls(school_id, community_colleges)

    major_data_dict = scrape_major_data(agreement_urls)

    unique_major_data = filter_duplicate_majors(major_data_dict)

    unique_major_data_with_abbreviations = [
        abbreviate_majors(major) for major in unique_major_data]

    sort_and_print_majors(
        unique_major_data, unique_major_data_with_abbreviations, school)

    for major_label, abbreviated_major in zip(unique_major_data, unique_major_data_with_abbreviations):
        grabber = PDFGrabber(
            school, school_id, major_label, abbreviated_major, delay)

        grabber.get_pdfs()

        cleaner = PDFCleaner(school)
        cleaner.extract_text()

        print(
            f"Major Label: {major_label}, Abbreviated Major: {abbreviated_major}")

    print("Program Ended")'''

if __name__ == '__main__':
    main()


'''
grabber = PDFGrabber('UCI', 120, 'Computer Science, B.S.', 'CS', 0.2)
grabber.get_pdfs()
cleaner = PDFCleaner()
cleaner.extract_text()

maker = DatabaseMaker('UCI', 'CS', id_to_key)
print("Database made succesfully")
maker.add_classes()
'''
