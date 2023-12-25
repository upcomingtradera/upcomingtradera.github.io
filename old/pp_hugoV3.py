import re
import os
import sys
import toml
import logging
import argparse
import multiprocessing
from PIL import Image, ImageOps
import pillow_avif

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URLIZE_PATTERN = re.compile(r'[^a-z0-9-]')

def urlize(s: str) -> str:
    """Emulate Hugo's urlize function."""
    s = s.lower().replace(" ", "-")
    s = URLIZE_PATTERN.sub('', s)
    s = re.sub(r'[-]+', '-', s)
    return s

def load_configuration(config_path: str) -> dict:
    """Load the TOML configuration file."""
    with open(config_path, 'r') as f:
        return toml.load(f)

def log_configuration(config):
    """Print the parsed configuration in a structured manner."""
    logger.info("\nConfiguration Details:")
    logger.info("----------------------")

    sections = ['settings', 'preprocess', 'input', 'output']
    for section in sections:
        logger.info(f"\n{section.capitalize()}:")
        for key, value in config.get(section, {}).items():
            logger.info(f"{key}: {value}")
    logger.info("----------------------\n")


def process_frontmatter(content, config, current_dir):
    """Process .md files with frontmatter format."""
    frontmatter = extract_frontmatter(content)
    image_path = frontmatter.get(config["input"]["key"])
    if not image_path:
        logger.info(f"Error: No image path found in frontmatter. Frontmatter content:\n{frontmatter}")
        return
    absolute_image_path = os.path.join(current_dir, image_path)
    
    config['frontmatter'] = frontmatter
    process_image(absolute_image_path, config)


def plain_format_handler():
    logger.info(f"plain format handler")
    pass


def image_format_handler(file_path, config):
    """Handler for image format."""
    
    # Open the image using PIL
    with Image.open(file_path) as img:
        
        # Iterate through the image types in the configuration
        for image_type in config["image_types"]:
            sizes = image_type["sizes"]
            postfixes = image_type["postfixes"]
            title = urlize(image_type["title"])
            
            # For each image type, resize the image based on the provided sizes
            for size, postfix in zip(sizes, postfixes):
                resized_img = resize_image(img, size)  # Assuming resize_image function is already defined
                
                # Save the resized image with the appropriate filename
                for format in config["settings"]["formats"]:
                    filename = config["output"]["filename_template"].format(
                        frontmatter_title=title,
                        settings_postfixes=postfix,
                        upper_format=format.upper(),
                        format=format
                    )
                    output_path = os.path.join(config["output"]["dir"], filename)
                    resized_img.save(output_path, format=format.upper())
                    logger.info(f"Saved resized image to {output_path}")


FORMAT_HANDLERS = {
    'frontmatter': process_frontmatter,
    'plain': plain_format_handler,
    'image': image_format_handler
    # Add other formats as needed
}

def worker(content, config, current_dir):
    try:
        format_name = config["preprocess"]["format"]
        handler = FORMAT_HANDLERS.get(format_name)
        if not handler:
            logger.error(f"Unsupported format: {format_name}")
            return
        handler(content, config, current_dir)
    except Exception as e:
        logger.error(f"Error processing content with format {format_name}. Error: {e}")



def load_file(file_path):
    """Load the content of a file."""
    with open(file_path, 'r') as f:
        return f.read()

def plain_format_handler(content, input_key, output_settings, settings):
    """Handler for plain format. Simply treats content as image path."""
    image_path = content.strip()  # Assuming the file contains only the image path
    process_image(image_path, output_settings, settings)


def is_valid_image(file_path):
    """Check if the file is a valid image."""
    try:
        with Image.open(file_path) as img:
            img.verify()  # This will check if the file is a valid image
        return True
    except Exception:
        return False


def handle_single_file(config):
    """Handle processing for a single file."""
    file_path = config["settings"]["path"]
    
    # Check if the file exists
    if not os.path.exists(file_path):
        logger.error(f"Error: File {file_path} does not exist.")
        return

    file_format = config["preprocess"]["format"]

    # If the format is "image", validate that the file is an image
    if file_format == "image":
        if not is_valid_image(file_path):
            logger.error(f"Error: File {file_path} is not a valid image.")
            return
    else:
        expected_filetype = config["preprocess"]["filetype"]
        # Check if the file is of the expected type
        if not file_path.endswith(expected_filetype):
            logger.error(f"Error: File {file_path} is not of expected type {expected_filetype}.")
            return

    # Iterate through the image types
    for image_type in config["image_types"]:
        sizes = image_type["sizes"]
        ratios = image_type["ratios"]
        postfixes = image_type["postfixes"]
        title = urlize(image_type["title"])
        print(title)
        
        """
        for size, ratio, postfix in zip(sizes, ratios, postfixes):
            config['output_settings'] = {
                'dir': config["output"]["dir"],
                'filename_template': config["output"]["filename_template"].format(
                    frontmatter_title=title,
                    settings_postfixes=postfix,
                    upper_format="{upper_format}",
                    format="{format}"
                )
            }
            process_image(file_path, config)
        """


def handle_directory(config):
    """Handle processing for directories."""
    directory_path = config["settings"]["path"]
    if not os.path.exists(directory_path):
        logger.error(f"Error: Directory {directory_path} does not exist.")
        return

    format_name = config["preprocess"]["format"]
    format_handler = FORMAT_HANDLERS.get(format_name)
    if not format_handler:
        logger.error(f"Unsupported format: {format_name}")
        return

    args_list = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                content = load_file(file_path)
                args_list.append((content, config, root))

    # Use multiprocessing to process the images in parallel
    with multiprocessing.Pool() as pool:
        pool.starmap(worker, args_list)


def handle_single_file(config):
    """Handle processing for a single file."""
    file_path = config["settings"]["path"]
    
    # Check if the file exists
    if not os.path.exists(file_path):
        logger.error(f"Error: File {file_path} does not exist.")
        return

    format_name = config["preprocess"]["format"]
    format_handler = FORMAT_HANDLERS.get(format_name)
    
    # Check if the format handler exists
    if not format_handler:
        logger.error(f"Unsupported format: {format_name}")
        return

    # If the format is "image", pass the file_path directly to the format_handler
    if format_name == "image":
        format_handler(file_path, config)
    else:
        content = load_file(file_path)
        format_handler(content, config)



def extract_frontmatter(file_content):
    frontmatter = {}
    # Check for YAML front matter
    if file_content.startswith('---'):
        frontmatter = yaml.safe_load(file_content.split('---')[1])
    # Check for TOML front matter
    elif file_content.startswith('+++'):
        frontmatter = toml.loads(file_content.split('+++')[1])
    # Check for JSON front matter
    elif file_content.startswith('{') and file_content.endswith('}'):
        frontmatter = json.loads(file_content)
    else:
        logger.info(f"""
        Failed to Parse content
        -----------------------
        {content}
        -----------------------
        """)
        sys.exit(1)
    return frontmatter

def generate_fingerprint(path):
    # Placeholder: Implement the logic to generate a fingerprint for a given path
    return "some_fingerprint"


def resize_image(img: Image.Image, size: str) -> Image.Image:
    """Resize the image based on the provided size."""
    dimensions = size.split('x')
    aspect_ratio = img.width / img.height
    
    try:
        width = int(dimensions[0]) if dimensions[0] else None
    except (ValueError, IndexError):
        width = None

    try:
        height = int(dimensions[1]) if dimensions[1] else None
    except (ValueError, IndexError):
        height = None

    # If both width and height are provided
    if width and height:
        return ImageOps.fit(img, (width, height), Image.LANCZOS)
    
    # If only width is provided
    elif width:
        height = int(width / aspect_ratio)
        return img.resize((width, height), Image.LANCZOS)
    
    # If only height is provided
    elif height:
        width = int(height * aspect_ratio)
        return img.resize((width, height), Image.LANCZOS)
    
    # If neither width nor height is provided
    else:
        logger.error("Neither width nor height provided for resizing. Exiting.")
        sys.exit(1)


def process_image_logic(image_path: str, config):
    """Process a single image based on the provided settings."""
    fm = config["frontmatter"]
    os_ = config["output"]
    formats = config["settings"]["formats"]

    with Image.open(image_path, mode="r") as img:
        for image_type in config["image_types"]:
            sizes = image_type["sizes"]
            postfixes = image_type["postfixes"]
            for size, postfix in zip(sizes, postfixes):
                img_resized = resize_image(img, size)
                for format in formats:
                    new_filename = os_['filename_template'].format(
                        frontmatter_title=urlize(fm['title']), 
                        settings_postfixes=postfix, 
                        upper_format=format.upper(), 
                        format=format
                    )
                    output_file = os.path.join(os_['dir'], new_filename)
                    try:
                        img_resized.save(output_file, format=format.upper())
                        logger.info(f"Processed\n{image_path}\nSaved: {output_file}\n")
                    except Exception as e:
                        logger.error(f"Exception: {str(e)}\nSkipping...\n")
    logger.info(f"Processed: {image_path}...")

def process_image(absolute_image_path, config):
    """Process a single image."""
    # Extracting necessary metadata
    title = config.get('name', 'default_title')
    image_type = config.get('type', 'default_type')
    config['output_settings'] = config["output"]
    process_image_logic(absolute_image_path, config)


def main(args):
    """Main function to handle the processing logic."""
    # Load the configuration
    config = load_configuration(args.config)
    
    # Print the parsed configuration
    log_configuration(config)

    # Branching logic based on the type using dictionaries
    type_handlers = {
        'directory': handle_directory,
        'single': handle_single_file
    }

    # Get the type handler based on the settings
    type_handler = type_handlers.get(config["settings"]["type"])
    if type_handler:
        type_handler(config)
    else:
        logger.error("Error: Invalid type specified in settings.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Preprocessor based on TOML configuration")
    parser.add_argument("--config", required=True, help="Path to the TOML configuration file")
    args = parser.parse_args()
    main(args)
