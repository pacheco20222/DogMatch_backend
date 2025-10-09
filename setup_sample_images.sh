#!/bin/bash

echo "🚀 DogMatch Sample Images Setup"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if requests module is available
if ! python3 -c "import requests" &> /dev/null; then
    echo "📦 Installing requests module..."
    pip3 install requests
fi

echo "📥 Downloading sample images..."
python3 download_sample_images.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sample images downloaded successfully!"
    echo ""
    echo "📁 Directory structure created:"
    echo "   sample_images/"
    echo "   ├── dog_photos/ (10 images)"
    echo "   ├── user_photos/ (10 images)"
    echo "   └── event_photos/ (5 images)"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Set up AWS credentials in Render"
    echo "   2. Run: python3 seed_with_s3_photos.py"
    echo "   3. Test the app with real photos!"
else
    echo "❌ Failed to download sample images"
    exit 1
fi
