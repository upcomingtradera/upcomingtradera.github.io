import csv
import os
import sys
from slugify import slugify

def create_hugo_content(csv_file_path):
    # Create TMP directory next to the current running program
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TMP')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Use the 'urlized' column for the folder name and convert to lowercase
            folder_path = os.path.join(output_dir, row['urlized'].lower())
            os.makedirs(folder_path, exist_ok=True)
            
            with open(os.path.join(folder_path, 'index.md'), 'w') as md_file:
                md_file.write('+++\n\n')
                md_file.write('type = "posts"\n')
                md_file.write(f'title = "{row["title"]}"\n')
                md_file.write(f'date = {row["date"]}\n')
                md_file.write('description = ""\n')
                md_file.write('draft = false\n')
                md_file.write('comment = true\n')
                md_file.write('toc = true\n')
                md_file.write('thumbnail = "feature.jpg"\n')
                md_file.write('authors = ["ut"]\n')
                md_file.write('\n+++\n')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <path_to_csv_file>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    create_hugo_content(csv_path)

