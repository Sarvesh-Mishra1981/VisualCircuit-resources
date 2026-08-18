"""
update_docs.py
--------------
This script automatically generates standalone HTML documentation pages for each custom block 
available in the Marketplace and updates the main Blocks.html index page with links to them. 

It runs automatically via a GitHub Action whenever a new block is pushed to the custom_blocks/ directory.

Workflow:
1. Reads `marketplace/registry.json` to discover all available custom blocks.
2. Extracts block metadata (name, description, author, ports) from each block's JSON code.
3. Dynamically injects this metadata into a reusable HTML template (modeled after the pdoc3 format).
4. Saves a new standalone HTML file for the block (e.g., `blockDocs/Blocks/Laser_Mapping.html`).
5. Updates the master index page (`blockDocs/Blocks.html`) to include a link to the new subpage.
"""

import os
import json
from bs4 import BeautifulSoup
import html

# Define paths relative to the repository root
REGISTRY_PATH = 'marketplace/registry.json'
HTML_PATH = 'blockDocs/Blocks.html'
CUSTOM_BLOCKS_DIR = 'custom_blocks/'
BLOCKS_DIR = 'blockDocs/Blocks/'

def get_template():
    """
    Extracts the base HTML structure from an existing pdoc3-generated file (Blur.html).
    This ensures that the dynamically generated pages have the exact same CSS styling 
    and layout as the rest of the documentation.
    """
    # Use Blur.html as a template for the page structure
    template_path = os.path.join(BLOCKS_DIR, 'Blur.html')
    if not os.path.exists(template_path):
        # Fallback to an empty template if Blur is missing
        return "<html><body>{MAIN_CONTENT}</body></html>"
        
    with open(template_path, 'r') as f:
        html_content = f.read()
        
    # Isolate the main content area of the template and replace it with a {MAIN_CONTENT} placeholder
    main_start = html_content.find('<main class="pdoc">')
    main_end = html_content.find('</main>', main_start) + len('</main>')
    
    if main_start != -1 and main_end != -1:
        return html_content[:main_start] + "{MAIN_CONTENT}" + html_content[main_end:]
    return "<html><body>{MAIN_CONTENT}</body></html>"

def generate_block_page(block_metadata, code, json_data, template):
    """
    Generates a dedicated HTML page for a custom block using its metadata.
    
    Args:
        block_metadata: Dictionary containing basic info from registry.json
        code: Python source code extracted from the block
        json_data: Full JSON representation of the .vc3 file to extract port information
        template: The HTML template string with a {MAIN_CONTENT} placeholder
    """
    # Extract basic info
    name = block_metadata.get('name', 'CustomBlock')
    description = block_metadata.get('description', 'No description provided.')
    author = block_metadata.get('author', 'Unknown Author')
    version = block_metadata.get('version', '1.0.0')
    category = block_metadata.get('category', 'Custom')

    # Parse the block's JSON to find input/output ports and parameters
    inputs = []
    outputs = []
    parameters = []
    
    if json_data:
        components = json_data.get('design', {}).get('graph', {}).get('blocks', [])
        for block in components:
            # We look for the 'basic.code' node inside the custom block to find ports
            if block.get('type') == 'basic.code':
                ports = block.get('data', {}).get('ports', {})
                inputs = [p.get('name') for p in ports.get('in', [])]
                outputs = [p.get('name') for p in ports.get('out', [])]
                params_data = block.get('data', {}).get('params', [])
                parameters = [p.get('name') for p in params_data]
                break

    # Format the extracted lists as comma-separated strings
    inputs_str = ', '.join(inputs) if inputs else 'None'
    outputs_str = ', '.join(outputs) if outputs else 'None'
    params_str = ', '.join(parameters) if parameters else 'None'

    # Escape the Python code so it displays safely in the HTML <pre> block
    escaped_code = html.escape(code)

    # Build the main content HTML structure mimicking pdoc3 output
    main_content = f"""<main class="pdoc">
    <section class="module-info">
        <h1 class="modulename">
            <a href="./../Blocks.html">Blocks</a><wbr>.{name}
        </h1>
    </section>
    <section id="section-intro">
        <div class="docstring">
            <p><strong>Author:</strong> {author} | <strong>Version:</strong> {version} | <strong>Category:</strong> {category}</p>
            <p>{description}</p>
            <p><strong>Inputs:</strong> {inputs_str}</p>
            <p><strong>Outputs:</strong> {outputs_str}</p>
            <p><strong>Parameters:</strong> {params_str}</p>
        </div>
    </section>
    <section>
        <h2 class="section-title" id="header-classes">Source Code</h2>
        <div class="pdoc-code codehilite"><pre><span></span><code>{escaped_code}</code></pre></div>
    </section>
</main>"""

    # Inject the content into the template and save the file
    page_html = template.replace("{MAIN_CONTENT}", main_content)
    out_path = os.path.join(BLOCKS_DIR, f"{name}.html")
    with open(out_path, 'w') as f:
        f.write(page_html)
    print(f"Generated {out_path}")

def update_index(registry):
    """
    Updates the master Blocks.html file by injecting links to the newly generated custom block pages.
    """
    with open(HTML_PATH, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Remove any old inline custom blocks that were injected in previous legacy versions of this script
    custom_header = soup.find('h2', id='custom-blocks-marketplace')
    if custom_header:
        custom_header.decompose()
    for custom_section in soup.find_all('section', class_='custom-block'):
        custom_section.decompose()

    # Find the nav sidebar where we will add the Custom Blocks section
    nav = soup.find('nav', class_='pdoc')
    if not nav:
        print("Could not find nav sidebar in Blocks.html")
        return
        
    nav_div = nav.find('div')
    if not nav_div:
        return

    # Find or create the "Custom Blocks" header and list
    custom_blocks_header = soup.find('h2', string='Custom Blocks')
    custom_blocks_list = None
    
    if not custom_blocks_header:
        custom_blocks_header = soup.new_tag('h2')
        custom_blocks_header.string = "Custom Blocks"
        custom_blocks_list = soup.new_tag('ul')
        
        # Insert before the attribution tag (the pdoc logo at the bottom of the sidebar)
        attribution = nav_div.find('a', class_='attribution')
        if attribution:
            attribution.insert_before(custom_blocks_header)
            attribution.insert_before(custom_blocks_list)
        else:
            nav_div.append(custom_blocks_header)
            nav_div.append(custom_blocks_list)
    else:
        custom_blocks_list = custom_blocks_header.find_next_sibling('ul')

    # Add a new link (<li><a>) for each custom block in the registry if it doesn't already exist
    for block in registry.get('blocks', []):
        name = block.get('name', 'Unknown')
        link_href = f"Blocks/{name}.html"
        
        # Check if the link is already in the list
        exists = False
        for a in custom_blocks_list.find_all('a'):
            if a.get('href') == link_href:
                exists = True
                break
                
        # Append the new link to the end of the list
        if not exists:
            new_li = soup.new_tag('li')
            new_a = soup.new_tag('a', href=link_href)
            new_a.string = name
            new_li.append(new_a)
            custom_blocks_list.append(new_li)
            print(f"Added link to Blocks.html sidebar: {name}")

    # Save the updated index file
    with open(HTML_PATH, 'w') as f:
        f.write(str(soup))
    print("Updated Blocks.html index")

def main():
    if not os.path.exists(REGISTRY_PATH):
        print(f"Registry not found at {REGISTRY_PATH}")
        return

    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)

    # Load the base HTML structure template
    template = get_template()

    # Iterate over all custom blocks listed in the marketplace registry
    for block in registry.get('blocks', []):
        name = block.get('name', 'Unknown')
        block_id = block.get('id', name)
        
        # We attempt to read the payload of the block to extract its source code
        # We check for both .vc3 and .json extensions
        code = "# Code not found"
        json_data = None
        
        for ext in ['.vc3', '.json']:
            json_path = os.path.join(CUSTOM_BLOCKS_DIR, f"{block_id}{ext}")
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        json_data = json.load(f)
                        
                        # Dig into the JSON structure to find the user's custom python code
                        components = json_data.get('design', {}).get('graph', {}).get('blocks', [])
                        for c in components:
                            if c.get('type') == 'basic.code':
                                code = c.get('data', {}).get('code', '')
                                break
                    break
                except Exception as e:
                    print(f"Error parsing {json_path}: {e}")
                
        # Generate the standalone HTML documentation page for this block
        generate_block_page(block, code, json_data, template)

    # Finally, update the main index file with links to all the newly generated pages
    update_index(registry)

if __name__ == '__main__':
    main()
