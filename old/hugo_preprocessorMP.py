import re
import os
import sys
import yaml
import toml
import json
import hashlib
import argparse
from PIL import Image
from PIL import ImageOps
import multiprocessing

import pillow_avif

content_dir = None
output_dir  = None
folder_fingerprints = {}

# Configuration
config = {
    "thumbnail_sizes": ["1280x720", "640x360", "320x180", "160x90"],
    "header_sizes": ["1280x", "640x", "320x", "160x"],
    "formats": ["jpeg", "webp", "png", "avif"],
    "thumbnail_postfixes": ["TL", "TM", "TS", "TES"],
    "header_postfixes": ["HL", "HM", "HS", "HES"]
}


def worker(image_data):
    image_path, image_type, title = image_data
    process_image(image_path, image_type, title)

def chunkify(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def parse_front_matter(file_content):
    # Check for YAML front matter
    if file_content.startswith('---'):
        return yaml.safe_load(file_content.split('---')[1])
    # Check for TOML front matter
    elif file_content.startswith('+++'):
        return toml.loads(file_content.split('+++')[1])
    # Check for JSON front matter
    elif file_content.startswith('{') and file_content.endswith('}'):
        return json.loads(file_content)
    else:
        return None

def urlize_test(title):
    return title.lower().replace(" ", "-").replace(":", "")

"""
this function emulates hugos urlize function
"""
def urlize(s: str) -> str:
    # Convert to lowercase
    s = s.lower()
    # Replace spaces with hyphens
    s = s.replace(" ", "-")
    # Remove any characters that are not alphanumeric or hyphens
    s = re.sub(r'[^a-z0-9-]', '', s)
    # Replace multiple consecutive hyphens with a single hyphen
    s = re.sub(r'-+', '-', s)
    return s

"""
def urlize(s: str) -> str:
    # Convert to lowercase
    s = s.lower()
    # Replace spaces with hyphens
    s = s.replace(" ", "-")
    # Remove any characters that are not alphanumeric or hyphens
    s = re.sub(r'[^a-z0-9-]', '', s)
    return s
"""

def generate_filename_fingerprint(filename):
    return hashlib.sha256(filename.encode()).hexdigest()

def generate_fingerprint(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def has_file_changed(file_path, stored_fingerprint_path, original_fingerprint):
    if not os.path.exists(stored_fingerprint_path):
        print(f"file {file_path} has changed\n")
        return True

    with open(stored_fingerprint_path, 'r') as f:
        stored_fingerprint = f.read().strip()

    print(f"Stored Fingerprint: {stored_fingerprint}")
    print(f"Original Fingerprint: {original_fingerprint}")
    return stored_fingerprint != original_fingerprint


def process_image_test(image_path, image_type, title):
    global output_dir
    global content_dir
    sizes = config[f"{image_type}_sizes"]
    postfixes = config[f"{image_type}_postfixes"]

    for index, size in enumerate(sizes):
        postfix = postfixes[index]
        for format in config["formats"]:
            # Construct the new filename
            new_filename = f"{title}-{postfix}.{format}"
            # Print the details
            print(f"\n")
            print(f"{os.path.basename(image_path)}")
            print(f"directory: {os.path.dirname(image_path)}")
            print(f"Processing {image_path}")
            print(f"{os.path.abspath(image_path)})")
            print(f"New filename: {new_filename}")
            # For now, let's use the new filename as the fingerprint (you can replace this with a real fingerprinting method later)
            fingerprint = generate_filename_fingerprint(new_filename)
            print(f"Fingerprint: {fingerprint}")
            print(f"Output directory: {output_dir}")
            output_file = f"{output_dir}/{new_filename}"
            print(f"Output file: {output_file}")

def process_image(image_path, image_type, title):
    global output_dir
    global folder_fingerprints
    sizes = config[f"{image_type}_sizes"]
    postfixes = config[f"{image_type}_postfixes"]

    folder_path = os.path.dirname(image_path)
    if folder_path not in folder_fingerprints:
        # Generate a fingerprint for the original image
        folder_fingerprints[folder_path] = generate_fingerprint(image_path)
    
    original_fingerprint = folder_fingerprints[folder_path]


    for index, size in enumerate(sizes):
        postfix = postfixes[index]
        for format in config["formats"]:
            # Construct the new filename
            new_filename = f"{title}-{postfix}.{format}"
            output_file = f"{output_dir}/{new_filename}"
            fingerprint_file = f"{output_file}.hash"
            # print(f"fingerprint_file {fingerprint_file}")
            print(f"prepping {output_file}")

            # Open the image
            with Image.open(image_path) as img:
                # Resize the image
                if image_type == "thumbnail":
                    # Smart fill for thumbnail sizes
                    width, height = map(int, size.split('x'))
                    img_resized = ImageOps.fit(img, (width, height), Image.LANCZOS)
                elif image_type == "header":
                    # Resize based on max width for header sizes
                    width = int(size[:-1])  # Remove the trailing 'x' and convert to int
                    aspect_ratio = img.width / img.height
                    height = int(width / aspect_ratio)
                    img_resized = img.resize((width, height))

                # Save the image in the desired format
                img_resized.save(output_file, format=format.upper())
                print(f"Processed and saved: {output_file}")

            """
            for index, size in enumerate(sizes):
                postfix = postfixes[index]
                for format in config["formats"]:
                    # Construct the new filename
                    new_filename = f"{title}-{postfix}.{format}"
                    output_file = f"{output_dir}/{new_filename}"
                    fingerprint_file = f"{output_file}.hash"
                    print(f"fingerprint_file {fingerprint_file}")

                    # Check if the file has changed
                    # if has_file_changed(image_path, fingerprint_file, original_fingerprint):
                    if True:
                        # Open the image
                        with Image.open(image_path) as img:
                            # Resize the image


                            if image_type == "thumbnail":
                                # Smart fill for thumbnail sizes
                                width, height = map(int, size.split('x'))
                                img_resized = ImageOps.fit(img, (width, height), Image.LANCZOS)
                            elif image_type == "header":
                                # Resize based on max width for header sizes
                                width = int(size[:-1])  # Remove the trailing 'x' and convert to int
                                aspect_ratio = img.width / img.height
                                height = int(width / aspect_ratio)
                                img_resized = img.resize((width, height))


                            # img = img.resize((width, height))
                            # Save the image in the desired format
                            img_resized.save(output_file, format=format.upper())
                            # Store the fingerprint of the new image
                            with open(fingerprint_file, 'w') as f:
                                f.write(original_fingerprint)

                        print(f"Processed and saved: {output_file}")
                    else:
                        print(f"File {output_file} has not changed. Skipping...")
            """


def main():
    global output_dir
    global content_dir

    parser = argparse.ArgumentParser(description="Image Preprocessor for Hugo")
    parser.add_argument("--content-dir", required=True, help="Directory to crawl for content")
    parser.add_argument("--output-dir", required=True, help="Directory where processed images will be saved")
    args = parser.parse_args()

    content_dir = os.path.abspath(args.content_dir)  # Convert to absolute path
    output_dir = os.path.abspath(args.output_dir)  # Convert to absolute path

    print(f"Content Directory: {content_dir}")
    print(f"Output Directory: {output_dir}")


    all_images = []
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    front_matter = parse_front_matter(content)
                    if front_matter:
                        raw_title = front_matter.get('title', '')
                        title = urlize(raw_title)
                        thumbnail = front_matter.get('thumbnail')
                        if thumbnail:
                            if isinstance(thumbnail, list):
                                for image in thumbnail:
                                    full_image_path = os.path.join(root, image)
                                    if not os.path.exists(full_image_path):
                                        print(f"Missing file: {full_image_path}")
                                        continue
                                    all_images.append((full_image_path, "thumbnail", title))
                                    all_images.append((full_image_path, "header", title))
                            else:
                                full_image_path = os.path.join(root, thumbnail)
                                if not os.path.exists(full_image_path):
                                    print(f"Missing file: {full_image_path}")
                                    continue
                                all_images.append((full_image_path, "thumbnail", title))
                                all_images.append((full_image_path, "header", title))

    num_cores = multiprocessing.cpu_count()
    with multiprocessing.Pool(num_cores) as pool:
        pool.map(worker, all_images)


if __name__ == "__main__":
    main()
