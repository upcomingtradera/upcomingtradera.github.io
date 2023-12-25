import re
import os
import sys
import toml
import argparse
import pillow_avif
import multiprocessing
from PIL import Image
from PIL import ImageOps

URLIZE_PATTERN = re.compile(r'[^a-z0-9-]')
folder_fingerprints = {}

def urlize(s: str) -> str:
    """Emulate Hugo's urlize function."""
    s = s.lower().replace(" ", "-")
    s = URLIZE_PATTERN.sub('', s)
    s = re.sub(r'[-]+', '-', s)
    return s

def load_configuration(config_path):
    """Load the TOML configuration file."""
    with open(config_path, 'r') as f:
        return toml.load(f)

def print_configuration(config):
    """Print the parsed configuration in a structured manner."""
    print("\nConfiguration Details:")
    print("----------------------")
    # Sections to print
    sections = ['settings', 'preprocess', 'input', 'output']
    for section in sections:
        print(f"\n{section.capitalize()}:")
        for key, value in config.get(section, {}).items():
            print(f"{key}: {value}")
    print("----------------------\n")


def process_frontmatter(content, input_key, output_settings, settings, current_dir):
    """Process .md files with frontmatter format."""
    frontmatter = extract_frontmatter(content)
    image_path = frontmatter.get(input_key)
    # print(f"""
    # frontmatter: {frontmatter}
    # image_path:  {image_path}
    # """)
    if not image_path:
        print(f"Error: No image path found in frontmatter. Frontmatter content:\n{frontmatter}")
        return
    absolute_image_path = os.path.join(current_dir, image_path)
    
    settings['frontmatter'] = frontmatter
    process_image(absolute_image_path, output_settings, settings)

def load_file(file_path):
    """Load the content of a file."""
    with open(file_path, 'r') as f:
        return f.read()

def plain_format_handler(content, input_key, output_settings, settings):
    """Handler for plain format. Simply treats content as image path."""
    image_path = content.strip()  # Assuming the file contains only the image path
    process_image(image_path, output_settings, settings)

def handle_single_file(settings, input_settings, output_settings, format_handler):
    """Handle processing for a single file."""
    file_path = settings.get('path')
    expected_filetype = settings.get('filetype', '.md')  # Default to .md if not specified
    file_format = settings.get('format', 'plain')  # Default to 'plain' if not specified
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    # Check if the file is of the expected type
    if not file_path.endswith(expected_filetype):
        print(f"Error: File {file_path} is not of expected type {expected_filetype}.")
        return

    # Load the content of the file
    content = load_file(file_path)

    # Process the content based on the format
    if file_format == 'plain':
        plain_format_handler(content, input_settings.get('key'), output_settings, settings)
    else:
        format_handler(content, input_settings.get('key'), output_settings, settings)


def handle_directory(settings, input_settings, output_settings, format_handler):
    """Handle processing for directories."""
    directory_path = settings.get('path')
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} does not exist.")
        return

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                content = load_file(file_path)
                format_handler(content, input_settings.get('key'), output_settings, settings, root)


def handle_single_file(settings, input_settings, output_settings, format_handler):
    """Handle processing for a single file."""
    file_path = settings.get('path')
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return
    content = load_file(file_path)
    format_handler(content, input_settings.get('key'), output_settings)

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
        print(f"""
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

def process_image_logic(image_path, image_type, title, settings, image_type_settings):
    global folder_fingerprints

    output_dir = image_type_settings['output_dir']
    sizes      = image_type_settings["sizes"]
    postfixes  = image_type_settings["postfixes"]
    formats    = image_type_settings["formats"]
    fm         = settings["frontmatter"]
    os_         = settings["output_settings"]
    # print(f"""
    # process_image_logic__output
    # output dir:          {output_dir}
    # sizes:               {sizes}
    # postfixes:           {postfixes}
    # formats:             {formats}
    # frontmatter:         {fm}
    # output settings:     {os_}
    # filename template:   {os_['filename_template']}
    # """)


    for index, size in enumerate(sizes):
        postfix = postfixes[index]
        for format in formats:
            postfix = postfixes[index]
            new_filename = os_['filename_template'].format(frontmatter_title=urlize(fm['title']), settings_postfixes=postfix, upper_format=format.upper(), format=format)
            output_file = os.path.join(output_dir, new_filename)
            # print(f"""
            # index:       {index}
            # size:        {size}
            # format:      {format}
            # postfix:     {postfix}
            # title:       {fm['title']}
            # new fn:      {new_filename}
            # output:      {output_file}
            # """)
            # sys.exit(0)
            # Open the image
            try:

                with Image.open(image_path, mode="r") as img:
                    # Split the size to get width and height
                    dimensions = size.split('x')
                    
                    # Safely convert to integers and check if they are greater than 0
                    try:
                        width = int(dimensions[0]) if int(dimensions[0]) > 0 else None
                    except (ValueError, IndexError):
                        width = None

                    try:
                        height = int(dimensions[1]) if int(dimensions[1]) > 0 else None
                    except (ValueError, IndexError):
                        height = None

                    # Resize logic
                    aspect_ratio = img.width / img.height
                    if width and height:
                        # Resize based on provided width and height while maintaining aspect ratio
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
                    print(f"Processed: {image_path}\nPaved: {output_file}\n")
            except Exception as e:
                print(f"Exception: {str(e)}\nSkipping...\n")


def process_image(absolute_image_path, output_settings, settings):
    """Process a single image."""
    # Extracting necessary metadata
    title = settings.get('name', 'default_title')
    image_type = settings.get('type', 'default_type')
    settings['output_settings'] = output_settings
    image_type_settings = {
        'output_dir': output_settings.get('dir', './'),
        'sizes': settings.get('sizes', []),
        'postfixes': settings.get('postfixes', []),
        'formats': settings.get('formats', [])
    }
    # print(f"""
    # Process a single image function
    # image path:          {absolute_image_path}
    # output settings:     {output_settings}
    # settings:            {settings}
    # ----------------------------------------
    # image type settings: {image_type_settings}
    # """)

    # Call the provided process_image function
    process_image_logic(absolute_image_path, image_type, title, settings, image_type_settings)




def main(args):
    """Main function to handle the processing logic."""
    # Load the configuration
    config = load_configuration(args.config)
    
    # Print the parsed configuration
    print_configuration(config)

    # Extract configuration details
    settings = config.get('settings', {})
    preprocess = config.get('preprocess', {})
    input_settings = config.get('input', {})
    output_settings = config.get('output', {})

    # Branching logic based on the type using dictionaries
    type_handlers = {
        'directory': handle_directory,
        'single': handle_single_file
    }
    
    format_handlers = {
        'frontmatter': process_frontmatter
        # Add other formats as needed
    }

    format_handler = format_handlers.get(preprocess.get('format'))
    if not format_handler:
        print(f"Error: Unsupported format {preprocess.get('format')} specified in preprocess.")
        return

    type_handler = type_handlers.get(settings.get('type'))
    if type_handler:
        # print(f"""type handler
        # settings:        {settings}
        # input settings:  {input_settings}
        # output settings: {output_settings}
        # format handler:  {preprocess.get('format')}
        # """)
        type_handler(settings, input_settings, output_settings, format_handler)
    else:
        print("Error: Invalid type specified in settings.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Preprocessor based on TOML configuration")
    parser.add_argument("--config", required=True, help="Path to the TOML configuration file")
    args = parser.parse_args()
    main(args)


