import os
import ast
import sys

# ... (get_imports_from_file function remains same)

def get_imports_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def get_all_imports(start_dir):
    all_imports = set()
    for root, dirs, files in os.walk(start_dir):
        # Ignore virtualenv directories and hidden folders
        dirs[:] = [d for d in dirs if not d.startswith('gemini_env') and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                all_imports.update(get_imports_from_file(file_path))
    return all_imports

def check_dependencies():
    # 1. Read requirements.txt
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            requirements = {line.strip().split('==')[0].split('>=')[0].lower() for line in f if line.strip()}
    else:
        requirements = set()

    # 2. Extract imports from source code
    src_imports = get_all_imports('src')
    
    # 3. Filter standard libraries
    try:
        std_libs = sys.stdlib_module_names
    except AttributeError:
        # Simplified list for older python
        std_libs = {
            'os', 'sys', 'json', 'time', 'datetime', 'math', 're', 'random', 'subprocess',
            'logging', 'typing', 'collections', 'pathlib', 'shutil', 'glob', 'pickle',
            'email', 'http', 'urllib', 'itertools', 'functools', 'contextlib', 'threading',
            'multiprocessing', 'platform', 'warnings', 'traceback', 'io', 'csv', 'sqlite3',
            'ast', 'hashlib', 'base64', 'uuid', 'calendar', 'argparse', 'copy', 'tempfile'
        }
    
    std_libs = set(std_libs) | {'dotenv'} # dotenv is third-party but handled via mapping below

    # Project specific local modules (src)
    local_modules = {'src', 'config', 'core', 'collectors', 'models', 'utils', 'scripts'}

    # Mapping for import name vs package name
    package_mapping = {
        'PIL': 'pillow',
        'bs4': 'beautifulsoup4',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'google': 'google-generativeai',
        'dotenv': 'python-dotenv',
        'cv2': 'opencv-python',
        'jwt': 'pyjwt',
        'jose': 'python-jose'
    }

    missing_packages = set()

    for module in src_imports:
        if module in std_libs:
            continue
        if module in local_modules:
            continue
        
        # Check mapping
        package_name = package_mapping.get(module, module).lower()

        # Check if package is in requirements
        found = False
        if package_name in requirements:
            found = True
        else:
            # Special Handling
            if module == 'google': 
                if 'google-generativeai' in requirements or 'google-api-python-client' in requirements:
                    found = True
            
        if not found:
            missing_packages.add(package_name)

    print("\n📦 Dependency Check Result:")
    if missing_packages:
        print("⚠️  Missing packages in requirements.txt:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
    else:
        print("✅ All dependencies seem to be covered.")

if __name__ == "__main__":
    check_dependencies()
