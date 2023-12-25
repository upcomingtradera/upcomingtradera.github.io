import re
import os
import sys
import toml
import hashlib
import argparse
import pillow_avif
import multiprocessing
from PIL import Image
from PIL import ImageOps

URLIZE_PATTERN = re.compile(r'[^a-z0-9-]')
folder_fingerprints = {}

def load_config(config_path):
    """Load configuration from a TOML file."""
    with open(config_path, 'r') as f:
        return toml.load(f)

def urlize(s: str) -> str:
    """Emulate Hugo's urlize function."""
    s = s.lower().replace(" ", "-")
    s = URLIZE_PATTERN.sub('', s)
    s = re.sub(r'[-]+', '-', s)
    return s

def worker(image_path, image_type, title, image_type_settings):
    """Worker function for multiprocessing."""
    process_image(image_path, image_type, title, config, image_type_settings)


def generate_fingerprint(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

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

def get_author_name_from_data(folder_name, author_dir):
    """Retrieve the author's name from the authors.toml file based on the folder name."""
    authors_data_path = os.path.join(author_dir, 'authors.toml')
    with open(authors_data_path, 'r') as f:
        authors_data = toml.load(f)
        print(authors_data)
        author_info = authors_data.get(folder_name)
        if author_info:
            return author_info.get('authors_filename')
    return None

def process_image(image_path, image_type, title, config, image_type_settings):
    global folder_fingerprints

    output_dir = image_type_settings['output_dir']
    sizes = image_type_settings["sizes"]
    postfixes = image_type_settings["postfixes"]

    folder_path = os.path.dirname(image_path)
    if folder_path not in folder_fingerprints:
        folder_fingerprints[folder_path] = generate_fingerprint(image_path)
    
    original_fingerprint = folder_fingerprints[folder_path]
    for index, size in enumerate(sizes):
        postfix = postfixes[index]
        for format in config['settings']["formats"]:
            new_filename = f"{title}-{postfix}.{format}"
            output_file = os.path.join(output_dir, new_filename)
            # Open the image
            with Image.open(image_path, mode="r") as img:
                # Split the size to get width and height
                dimensions = size.split('x')
                width = dimensions[0]
                height = dimensions[1] if len(dimensions) > 1 else None

                # Check if width and height are valid integers
                try:
                    width = int(width)
                except ValueError:
                    width = None

                try:
                    height = int(height)
                except ValueError:
                    height = None

                # Resize logic
                aspect_ratio = img.width / img.height
                if width and height:
                    # Resize based on provided width and height while maintaining aspect ratio
                    max_size = (width, height)
                    img_resized = ImageOps.fit(img, (width, height), Image.LANCZOS)
                elif width:
                    # Resize based on provided width and maintain aspect ratio
                    height = int(width / aspect_ratio)
                    img.thumbnail((width, height), Image.LANCZOS)
                    img_resized = img
                elif height:
                    # Resize based on provided height and maintain aspect ratio
                    width = int(height * aspect_ratio)
                    img_resized = ImageOps.fit(img, (width, height), Image.LANCZOS)

                img_resized.save(output_file, format=format.upper())
                print(f"Processed and saved: {output_file}")


def load_organization_details(org_config_path):
    """Load the organization's details from the organization.toml file."""
    if os.path.exists(org_config_path):
        with open(org_config_path, 'r') as f:
            org_data = toml.load(f)
            org_info = org_data.get('organization', {})
            org_name = org_info.get('name', '')
            logo_filename = org_info.get('logo_file', '')
            return org_name, logo_filename
    return '', ''



def determine_image_type(image_path):
    if "thumbnail" in image_path:
        return "thumbnail"
    elif "header" in image_path:
        return "header"
    elif "authorbox" in image_path:
        return "authorbox"
    elif "org_logo" in image_path:
        return "org_logo"
    else:
        print(f"Does not have image type for path {image_path}...\n")
        sys.exit(1)


def process_md_images(root, files, image_type, image_type_settings, all_images, processed_images):
    for file in files:
        if file.endswith(".md"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                content = f.read()
                front_matter = parse_front_matter(content)
                if front_matter:
                    raw_title = front_matter.get('title', '')
                    title = urlize(raw_title)
                    thumbnail = front_matter.get('thumbnail')
                    if thumbnail:
                        process_thumbnail(thumbnail, root, image_type, title, image_type_settings, all_images, processed_images)

                    if image_type == 'authorbox':
                        process_authorbox(root, image_type, image_type_settings, all_images, processed_images)


def process_thumbnail(thumbnail, root, image_type, title, image_type_settings, all_images, processed_images):
    if isinstance(thumbnail, list):
        for image in thumbnail:
            full_image_path = os.path.join(root, image)
            add_image_to_process(full_image_path, image_type, title, image_type_settings, all_images, processed_images)
    else:
        full_image_path = os.path.join(root, thumbnail)
        add_image_to_process(full_image_path, image_type, title, image_type_settings, all_images, processed_images)


def process_authorbox(root, image_type, image_type_settings, all_images, processed_images):
    folder_name = os.path.basename(root)
    author_avatar_filename = get_author_name_from_data(folder_name, image_type_settings.get('author_dir', ''))
    if author_avatar_filename:
        full_image_path = os.path.join(root, author_avatar_filename)
        add_image_to_process(full_image_path, image_type, urlize(folder_name), image_type_settings, all_images, processed_images)


def add_image_to_process(full_image_path, image_type, title, image_type_settings, all_images, processed_images):
    if os.path.exists(full_image_path) and (full_image_path, image_type) not in processed_images:
        all_images.append((full_image_path, image_type, title, image_type_settings))
        processed_images.add((full_image_path, image_type))


def preprocess_images(config):
    all_images = []
    processed_images = set()

    for image_type_settings in config["settings"]["image_types"]:
        image_type = image_type_settings["name"]
        content_dir = image_type_settings["content_dir"]

        if image_type == 'org_logo':
            org_config_path = image_type_settings.get('org_config')
            org_name, logo_filename = load_organization_details(org_config_path)
            original_image_path = os.path.join(content_dir, logo_filename)
            print(original_image_path)
            
            if os.path.exists(original_image_path):
                urlized_logo_filename = urlize(logo_filename.rsplit('.', 1)[0])  # Urlize the filename without extension

                for postfix in image_type_settings.get('postfixes', []):
                    modified_filename = f"{urlized_logo_filename}-{postfix}.{logo_filename.rsplit('.', 1)[1]}"  # Append postfix and retain the original extension
                    full_image_path = os.path.join(content_dir, modified_filename)
                    
                    if (full_image_path, image_type) not in processed_images:
                        all_images.append((original_image_path, image_type, urlize(org_name), image_type_settings))
                        processed_images.add((full_image_path, image_type))
        else:
            for root, _, files in os.walk(content_dir):
                process_md_images(root, files, image_type, image_type_settings, all_images, processed_images)

    num_cores = multiprocessing.cpu_count()
    with multiprocessing.Pool(num_cores) as pool:
        pool.starmap(worker, all_images)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Preprocessor for Hugo")
    parser.add_argument("--config", required=True, help="Path to the configuration file")
    args = parser.parse_args()

    config = load_config(args.config)

    if not config.get("settings") or not config["settings"].get("image_types"):
        print("Error: Invalid configuration format.")
        exit(1)

    preprocess_images(config)
