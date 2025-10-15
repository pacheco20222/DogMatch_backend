#!/usr/bin/env python3
"""
Master script to reseed the database with fresh data.
This script will:
1. Clear all existing data
2. Upload sample images to S3
3. Create fresh seed data with users, dogs, matches, and messages
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the complete reseeding process"""
    print("🚀 Starting DogMatch Database Reseeding Process")
    print("=" * 60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Step 1: Clear existing data
        print("Step 1: Clearing existing data...")
        from clear_database import clear_database
        clear_database()
        print()
        
        # Step 2: Upload sample images to S3
        print("Step 2: Uploading sample images to S3...")
        from upload_samples_to_s3 import upload_sample_images
        upload_sample_images()
        print()
        
        # Step 3: Create fresh seed data
        print("Step 3: Creating fresh seed data...")
        from seed_fresh_data import seed_database
        seed_database()
        print()
        
        print("🎉 Database reseeding completed successfully!")
        print("=" * 60)
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🔑 Test Login Credentials:")
        print("  Admin: admin@dogmatch.com / admin123")
        print("  Shelter: shelter@dogmatch.com / shelter123")
        print("  Users: [username]@example.com / password123")
        print()
        print("📱 You can now test the app with fresh data!")
        
    except Exception as e:
        print(f"❌ Error during reseeding process: {str(e)}")
        print("🔄 Please check the error and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
