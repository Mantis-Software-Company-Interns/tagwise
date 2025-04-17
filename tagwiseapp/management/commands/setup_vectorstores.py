from django.core.management.base import BaseCommand
import os
import shutil
import stat

class Command(BaseCommand):
    help = 'Setup directories and permissions for vectorstores'
    
    def handle(self, *args, **options):
        # Define vectorstore directory path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        vectorstore_dir = os.path.join(base_dir, 'data', 'vectorstores')
        
        self.stdout.write(f"Setting up vectorstore directory at: {vectorstore_dir}")
        
        # Check if directory exists and create if it doesn't
        if not os.path.exists(vectorstore_dir):
            try:
                os.makedirs(vectorstore_dir)
                self.stdout.write(self.style.SUCCESS(f"Created vectorstore directory: {vectorstore_dir}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create vectorstore directory: {str(e)}"))
                return
        else:
            self.stdout.write(f"Vectorstore directory already exists.")
        
        # Check permissions
        try:
            # Get current permissions
            current_permissions = stat.S_IMODE(os.stat(vectorstore_dir).st_mode)
            required_permissions = current_permissions | stat.S_IRWXU  # Add read, write, execute for owner
            
            if current_permissions != required_permissions:
                os.chmod(vectorstore_dir, required_permissions)
                self.stdout.write(self.style.SUCCESS("Updated directory permissions to ensure write access"))
            else:
                self.stdout.write("Directory permissions are already correctly set")
                
            # Try to write a test file
            test_file = os.path.join(vectorstore_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('Test write permission')
            
            # Clean up test file
            os.remove(test_file)
            self.stdout.write(self.style.SUCCESS("Successfully verified write permissions"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Permission or access error: {str(e)}"))
            self.stdout.write("You may need to manually set correct permissions on the directory")
            
        # Setup complete
        self.stdout.write(self.style.SUCCESS("Vectorstore directory setup complete!"))
        self.stdout.write("You can now run the test_embeddings and index_bookmarks commands.") 