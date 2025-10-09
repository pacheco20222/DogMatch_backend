#!/usr/bin/env python3
"""
Sample Image Downloader for DogMatch
Downloads sample images from Unsplash for testing purposes.
"""

import requests
import os
import time

# Sample images directory
SAMPLE_IMAGES_DIR = "sample_images"

def download_image(url, filepath):
    """Download an image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {os.path.basename(filepath)}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {os.path.basename(filepath)}: {e}")
        return False

def download_sample_images():
    """Download sample images for testing"""
    print("📥 Downloading sample images for DogMatch testing...")
    
    # Create directories
    os.makedirs(os.path.join(SAMPLE_IMAGES_DIR, 'dog_photos'), exist_ok=True)
    os.makedirs(os.path.join(SAMPLE_IMAGES_DIR, 'user_photos'), exist_ok=True)
    os.makedirs(os.path.join(SAMPLE_IMAGES_DIR, 'event_photos'), exist_ok=True)
    
    # Dog photos (from Unsplash - free to use)
    dog_photos = [
        "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1547407139-3c921a71905c?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1551717743-49959800b1f6?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1547407139-3c921a71905c?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1551717743-49959800b1f6?w=400&h=400&fit=crop&crop=face"
    ]
    
    # User photos (from Unsplash - free to use)
    user_photos = [
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face"
    ]
    
    # Event photos (from Unsplash - free to use)
    event_photos = [
        "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400&h=300&fit=crop",
        "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=400&h=300&fit=crop",
        "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=300&fit=crop",
        "https://images.unsplash.com/photo-1547407139-3c921a71905c?w=400&h=300&fit=crop",
        "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=300&fit=crop"
    ]
    
    # Download dog photos
    print("\n🐕 Downloading dog photos...")
    for i, url in enumerate(dog_photos, 1):
        filepath = os.path.join(SAMPLE_IMAGES_DIR, 'dog_photos', f'dog{i}.jpg')
        download_image(url, filepath)
        time.sleep(0.5)  # Be nice to Unsplash
    
    # Download user photos
    print("\n👤 Downloading user photos...")
    for i, url in enumerate(user_photos, 1):
        filepath = os.path.join(SAMPLE_IMAGES_DIR, 'user_photos', f'user{i}.jpg')
        download_image(url, filepath)
        time.sleep(0.5)  # Be nice to Unsplash
    
    # Download event photos
    print("\n🎉 Downloading event photos...")
    for i, url in enumerate(event_photos, 1):
        filepath = os.path.join(SAMPLE_IMAGES_DIR, 'event_photos', f'event{i}.jpg')
        download_image(url, filepath)
        time.sleep(0.5)  # Be nice to Unsplash
    
    print(f"\n✅ Sample images downloaded to {SAMPLE_IMAGES_DIR}/")
    print("📁 Directory structure:")
    print("   sample_images/")
    print("   ├── dog_photos/ (10 images)")
    print("   ├── user_photos/ (10 images)")
    print("   └── event_photos/ (5 images)")
    
    print("\n🚀 You can now run: python seed_with_s3_photos.py")

if __name__ == '__main__':
    try:
        download_sample_images()
    except Exception as e:
        print(f"❌ Error downloading images: {e}")
        import traceback
        traceback.print_exc()
