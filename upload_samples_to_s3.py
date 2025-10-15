#!/usr/bin/env python3
"""
Upload sample images from the sample_images directory to S3 bucket.
This script will upload all images to the appropriate S3 folders.
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.s3_service import s3_service

def upload_sample_images():
    """Upload all sample images to S3"""
    app = create_app()
    
    with app.app_context():
        try:
            print("📤 Starting S3 upload of sample images...")
            
            # Define the sample images directory
            sample_images_dir = os.path.join(os.path.dirname(__file__), 'sample_images')
            
            # Upload dog photos
            dog_photos_dir = os.path.join(sample_images_dir, 'dog_photos')
            if os.path.exists(dog_photos_dir):
                print("🐕 Uploading dog photos...")
                dog_photos = [f for f in os.listdir(dog_photos_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                for photo in dog_photos:
                    photo_path = os.path.join(dog_photos_dir, photo)
                    s3_key = f"dog-photos/{photo}"
                    
                    try:
                        # Read file data
                        with open(photo_path, 'rb') as f:
                            file_data = f.read()
                        
                        # Upload using the correct method
                        result = s3_service.upload_photo(
                            file_data=file_data,
                            file_type='dog_photo',
                            user_id=1,  # Dummy user ID for seeding
                            dog_id=1    # Dummy dog ID for seeding
                        )
                        
                        if result['success']:
                            print(f"  ✅ Uploaded {photo} -> {s3_key}")
                        else:
                            print(f"  ❌ Failed to upload {photo}: {result['error']}")
                    except Exception as e:
                        print(f"  ❌ Failed to upload {photo}: {str(e)}")
            
            # Upload user photos
            user_photos_dir = os.path.join(sample_images_dir, 'user_photos')
            if os.path.exists(user_photos_dir):
                print("👤 Uploading user photos...")
                user_photos = [f for f in os.listdir(user_photos_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                for photo in user_photos:
                    photo_path = os.path.join(user_photos_dir, photo)
                    s3_key = f"user-photos/{photo}"
                    
                    try:
                        # Read file data
                        with open(photo_path, 'rb') as f:
                            file_data = f.read()
                        
                        # Upload using the correct method
                        result = s3_service.upload_photo(
                            file_data=file_data,
                            file_type='user_profile',
                            user_id=1  # Dummy user ID for seeding
                        )
                        
                        if result['success']:
                            print(f"  ✅ Uploaded {photo} -> {s3_key}")
                        else:
                            print(f"  ❌ Failed to upload {photo}: {result['error']}")
                    except Exception as e:
                        print(f"  ❌ Failed to upload {photo}: {str(e)}")
            
            # Upload event photos
            event_photos_dir = os.path.join(sample_images_dir, 'event_photos')
            if os.path.exists(event_photos_dir):
                print("🎉 Uploading event photos...")
                event_photos = [f for f in os.listdir(event_photos_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                
                for photo in event_photos:
                    photo_path = os.path.join(event_photos_dir, photo)
                    s3_key = f"event-photos/{photo}"
                    
                    try:
                        # Read file data
                        with open(photo_path, 'rb') as f:
                            file_data = f.read()
                        
                        # Upload using the correct method
                        result = s3_service.upload_photo(
                            file_data=file_data,
                            file_type='event_photo',
                            user_id=1,  # Dummy user ID for seeding
                            event_id=1  # Dummy event ID for seeding
                        )
                        
                        if result['success']:
                            print(f"  ✅ Uploaded {photo} -> {s3_key}")
                        else:
                            print(f"  ❌ Failed to upload {photo}: {result['error']}")
                    except Exception as e:
                        print(f"  ❌ Failed to upload {photo}: {str(e)}")
            
            print("✅ S3 upload completed successfully!")
            print(f"📊 Uploaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ Error uploading to S3: {str(e)}")
            raise

if __name__ == "__main__":
    upload_sample_images()
