"""
update_registry.py
------------------
This script automatically scans the `custom_blocks` directory for any uploaded 
.vc3 or .json files, extracts their metadata, and updates the `marketplace/registry.json` file.

The `registry.json` file acts as the single source of truth for the VisualCircuit frontend 
Marketplace. Whenever a user clicks the "Marketplace" button in the frontend, it fetches 
this JSON file to populate the list of available blocks.

It runs automatically via a GitHub Action whenever a new block is pushed to the custom_blocks/ directory.
"""

import json
import os
import glob

def main():
    # Define directories relative to the repository root
    blocks_dir = "custom_blocks" # Directory where users upload their custom .vc3 / .json blocks
    registry_path = "marketplace/registry.json" # The registry file that the frontend consumes
    
    blocks = []

    # Recursively scan the custom_blocks folder for any .vc3 or .json files
    # The VisualCircuit editor allows exporting blocks as both .vc3 (graphical) and .json (code/ports).
    search_pattern = glob.glob(f"{blocks_dir}/**/*.vc3", recursive=True) + glob.glob(f"{blocks_dir}/**/*.json", recursive=True)
    
    for filepath in search_pattern:
        try:
            # Open and parse the JSON block payload
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # The user's metadata (Name, Description, Version) is stored in the "package" object
            pkg = data.get("package", {})
            
            # Use the physical file name (without extension) as the unique ID for the registry
            basename = os.path.basename(filepath)
            block_id = os.path.splitext(basename)[0]
            
            # Construct the raw download URL that the React frontend will use to fetch this block
            # NOTE: For official production deployment, this points to JdeRobot's main branch.
            repo = os.environ.get('GITHUB_REPOSITORY', 'JdeRobot/VisualCircuit-resources')
            url = f"https://raw.githubusercontent.com/{repo}/main/custom_blocks/{basename}"
            
            # Build the registry entry exactly as the frontend Validator expects it
            block_entry = {
                "id": block_id,
                "name": pkg.get("name", "Untitled"),
                "author": pkg.get("author", "Unknown"),
                "version": pkg.get("version", "1.0.0"),
                "description": pkg.get("description", ""),
                "category": pkg.get("category", "Uncategorized"),
                "tags": pkg.get("tags", []),
                "url": url
            }
            
            blocks.append(block_entry)
            print(f"Added {block_entry['name']} to registry.")
            
        except Exception as e:
            print(f"Failed to process {filepath}: {e}")
            
    # Wrap the list in a "blocks" object for the final JSON payload
    registry = {
        "blocks": blocks
    }
    
    # Save the updated registry back to disk
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
        
    print(f"Successfully generated registry.json with {len(blocks)} blocks.")

if __name__ == "__main__":
    main()
