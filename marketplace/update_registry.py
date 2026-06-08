import json
import os
import glob

def main():
    blocks_dir = "marketplace/blocks"
    registry_path = "marketplace/registry.json"
    
    blocks = []
    
    # Search for all .vc3 files
    for filepath in glob.glob(f"{blocks_dir}/**/*.vc3", recursive=True) + glob.glob(f"{blocks_dir}/**/*.json", recursive=True):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            pkg = data.get("package", {})
            
            # Use filename as ID
            basename = os.path.basename(filepath)
            block_id = os.path.splitext(basename)[0]
            
            # The download URL for the raw file on GitHub
            url = f"https://raw.githubusercontent.com/Sarvesh-Mishra1981/VisualCircuit-resources/main/marketplace/blocks/{basename}"
            
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
            
    registry = {
        "blocks": blocks
    }
    
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
        
    print(f"Successfully generated registry.json with {len(blocks)} blocks.")

if __name__ == "__main__":
    main()
