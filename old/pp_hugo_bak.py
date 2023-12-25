import re
import os
import toml
import hashlib
import argparse
import pillow_avif
import multiprocessing
from PIL import Image
from PIL import ImageOps

folder_fingerprints = {}

def load_config(config_path):
    """Load configuration from a TOML file."""
    with open(config_path, 'r') as f:
        return toml.load(f)

def urlize(s: str) -> str:
    """Emulate Hugo's urlize function."""
    s = s.lower().replace(" ", "-")
    return re.sub(r'[^a-z0-9-]', '', s)

def worker(image_data, config):
    """Worker function for multiprocessing."""
    image_path, image_type, title = image_data
    process_image(image_path, image_type, title, config)

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
        author_info = authors_data.get(folder_name)
        if author_info:
            return author_info.get('name')
    return None


def process_image(image_path, image_type, title, config):
    global folder_fingerprints

    # Find the correct image type settings from the config
    image_type_settings = next((item for item in config['settings']['image_types'] if item["name"] == image_type), None)

    if not image_type_settings:
        print(f"Settings for image type {image_type} not found in config.")
        return

    output_dir = image_type_settings['output_dir']
    sizes = image_type_settings["sizes"]
    postfixes = image_type_settings["postfixes"]

    folder_path = os.path.dirname(image_path)
    if folder_path not in folder_fingerprints:
        # Generate a fingerprint for the original image
        folder_fingerprints[folder_path] = generate_fingerprint(image_path)
    
    original_fingerprint = folder_fingerprints[folder_path]

    for index, size in enumerate(sizes):
        postfix = postfixes[index]
        for format in config['settings']["formats"]:
            # Construct the new filename
            new_filename = f"{title}-{postfix}.{format}"
            print(output_dir)
            print(new_filename)
            output_file = os.path.join(output_dir, new_filename)
            fingerprint_file = f"{output_file}.hash"
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

def preprocess_images(config):
    all_images = []

    for image_type_settings in config["settings"]["image_types"]:
        image_type = image_type_settings["name"]
        content_dir = image_type_settings["content_dir"]
        output_dir = image_type_settings["output_dir"]

        for root, _, files in os.walk(content_dir):
            # Check if we are processing author images
            if 'authors' in root:
                folder_name = os.path.basename(root)
                authorbox_settings = next((item for item in config['settings']['image_types'] if item["name"] == 'authorbox'), None)
                author_name = authorbox_settings.get('author_dir', '')
                if not author_name:
                    print(f"No matching author data found for folder: {folder_name}")
                    continue
                title = urlize(author_name)
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
                                        full_image_path = os.path.join(content_dir, root, image)
                                        if not os.path.exists(full_image_path):
                                            print(f"Missing file: {full_image_path}")
                                            continue
                                        all_images.append((full_image_path, "thumbnail", title))
                                        all_images.append((full_image_path, "header", title))
                                else:
                                    full_image_path = os.path.join(content_dir, root, thumbnail)
                                    if not os.path.exists(full_image_path):
                                        print(f"Missing file: {full_image_path}")
                                        continue
                                    all_images.append((full_image_path, "thumbnail", title))
                                    all_images.append((full_image_path, "header", title))

        num_cores = multiprocessing.cpu_count()
        with multiprocessing.Pool(num_cores) as pool:
            pool.starmap(worker, [(img_data, config) for img_data in all_images])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Preprocessor for Hugo")
    parser.add_argument("--config", required=True, help="Path to the configuration file")
    args = parser.parse_args()

    # Load configuration from file
    config = load_config(args.config)

    # Check if the configuration has the required settings
    if not config.get("settings") or not config["settings"].get("image_types"):
        print("Error: Invalid configuration format.")
        exit(1)

    print(config)
    preprocess_images(config)
