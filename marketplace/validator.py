import sys
import json
import ast

def validate_level_1(data):
    """Level 1: Metadata Validation"""
    print("[Level 1] Checking Metadata...")
    if "package" not in data:
        raise ValueError("Error (Level 1): Missing 'package' metadata. Please use 'Edit Project Info' in VisualCircuit.")
    
    pkg = data["package"]
    name = pkg.get("name", "").strip()
    desc = pkg.get("description", "").strip()
    category = pkg.get("category", "").strip()
    tags = pkg.get("tags", [])
    
    if not name or name == "Project" or name == "Untitled":
        raise ValueError("Error (Level 1): You must provide a valid Name before publishing.")
        
    if not desc:
        raise ValueError("Error (Level 1): You must provide a Description before publishing.")

    ALLOWED_CATEGORIES = ["Computer Vision", "Control Systems", "Locomotion", "Machine Learning", "Utilities", "ROS2"]
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Error (Level 1): Invalid or missing Category. Must be one of {ALLOWED_CATEGORIES}.")

    if not tags or not isinstance(tags, list):
        raise ValueError("Error (Level 1): You must provide at least one Tag before publishing.")

    print(f"Valid Package: {name} ({category})")

def validate_level_2(data):
    """Level 2: Structural & Wire Validation"""
    print("[Level 2] Checking Structure and Wires...")
    try:
        blocks = data["design"]["graph"]["blocks"]
        wires = data["design"]["graph"]["wires"]
    except KeyError:
        raise ValueError("Error (Level 2): Invalid block structure. Missing 'design.graph.blocks' or 'wires'.")

    # Removed: We no longer require a 'basic.code' node, 
    # as users can build blocks purely out of other built-in blocks (like camera -> drive).

    # Find all basic.input and basic.output nodes
    input_nodes = {b["id"]: b for b in blocks if b.get("type") == "basic.input"}
    output_nodes = {b["id"]: b for b in blocks if b.get("type") == "basic.output"}
    
    # Check if they are wired
    wired_blocks = set()
    for w in wires:
        wired_blocks.add(w["source"]["block"])
        wired_blocks.add(w["target"]["block"])
        
    for nid in input_nodes:
        if nid not in wired_blocks:
            raise ValueError(f"Error (Level 2): Found a disconnected basic.input node. Please wire it up.")
            
    for nid in output_nodes:
        if nid not in wired_blocks:
            raise ValueError(f"Error (Level 2): Found a disconnected basic.output node. Please wire it up.")
            
    # If there is more than 1 block, make sure NO block is left floating disconnected!
    if len(blocks) > 1:
        for b in blocks:
            if b["id"] not in wired_blocks:
                raise ValueError(f"Error (Level 2): Found a disconnected block '{b.get('type')}'. All blocks must be wired to something!")
            
    print("Structure and wires are valid.")

def validate_level_3(data):
    """Level 3: Python Syntax & Security Validation"""
    print("[Level 3] Checking Python Syntax and Security...")
    blocks = data["design"]["graph"]["blocks"]
    
    for block in blocks:
        if block.get("type") == "basic.code":
            code_str = block.get("data", {}).get("code", "")
            if not code_str.strip():
                raise ValueError("Error (Level 3): Code block is empty.")
            
            # 1. Check syntax using AST
            try:
                tree = ast.parse(code_str)
            except SyntaxError as e:
                raise ValueError(f"Error (Level 3): Python Syntax Error on line {e.lineno}: {e.msg}")
                
            # 2. Security Check: Search for blacklisted imports
            blacklist = ['os', 'subprocess', 'sys', 'shutil']
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in blacklist:
                            raise ValueError(f"Error (Level 3): Security Violation! Importing '{alias.name}' is not allowed.")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in blacklist:
                        raise ValueError(f"Error (Level 3): Security Violation! Importing from '{node.module}' is not allowed.")
                        
    print("Python code is syntactically correct and secure.")

def main(filepath):
    print(f"Validating {filepath}...\n" + "-"*40)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Could not read or parse JSON file: {e}")
        sys.exit(1)
        
    try:
        validate_level_1(data)
        validate_level_2(data)
        validate_level_3(data)
        print("-" * 40)
        print("Validation Successful! Block is safe to merge.")
    except ValueError as e:
        print("-" * 40)
        print(f"❌ Validation Failed!\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validator.py <path_to_block.vc3>")
        sys.exit(1)
    main(sys.argv[1])
