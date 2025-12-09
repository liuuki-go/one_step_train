import os
import sys

# Add root to path to ensure we can find the file name constant if we wanted to import it, 
# but for simplicity we know it's .activation in the project root.

ACTIVATION_FILE_NAME = "license"

def reset_activation():
    # Construct absolute path relative to project root
    # Assuming this script is in tools/ and project root is one level up
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    file_path = os.path.join(root_dir, ACTIVATION_FILE_NAME)
    
    print(f"Looking for activation file at: {file_path}")
    
    if os.path.exists(file_path):
        try:
            # Try to remove hidden attribute first just in case, though remove usually works
            if os.name == 'nt':
                os.system(f'attrib -h "{file_path}"')
            
            os.remove(file_path)
            print("Successfully removed activation file. App is now deactivated.")
        except Exception as e:
            print(f"Error removing file: {e}")
            print("Try running this script as Administrator.")
    else:
        # Also try to remove old .activation file if exists, to clean up
        old_file_path = os.path.join(root_dir, ".activation")
        if os.path.exists(old_file_path):
            try:
                if os.name == 'nt':
                    os.system(f'attrib -h "{old_file_path}"')
                os.remove(old_file_path)
                print("Removed old .activation file.")
            except:
                pass
                
        print("Activation file not found. App is already deactivated or never activated.")

if __name__ == "__main__":
    reset_activation()
    input("\nPress Enter to exit...")
