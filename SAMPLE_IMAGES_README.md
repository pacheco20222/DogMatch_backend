# 📸 Sample Images Setup for DogMatch

This directory contains sample images for testing the DogMatch app with real photos uploaded to S3.

## 📁 Directory Structure

```
sample_images/
├── dog_photos/          # 10 sample dog photos
├── user_photos/         # 10 sample user profile photos  
└── event_photos/        # 5 sample event banner photos
```

## 🚀 Quick Setup

### Option 1: Download Sample Images (Recommended)
```bash
# Download sample images from Unsplash
python download_sample_images.py

# Seed database with S3 photos
python seed_with_s3_photos.py
```

### Option 2: Add Your Own Images
1. Add your own images to the respective folders
2. Supported formats: `.jpg`, `.jpeg`, `.png`, `.gif`
3. Recommended size: 400x400px for user/dog photos, 400x300px for events
4. Run the seeding script: `python seed_with_s3_photos.py`

## 🔧 What the Seeding Script Does

1. **Clears database** - Removes all existing data
2. **Creates users** - Registers 11 test users (owners, admin, shelters)
3. **Uploads profile photos** - Uses sample user photos from `user_photos/`
4. **Creates dogs** - Each owner gets 1-3 dogs with random data
5. **Uploads dog photos** - Uses sample dog photos from `dog_photos/`
6. **Creates swipes** - Generates some initial swipes for testing

## 🧪 Test Credentials

After seeding, you can test with these accounts:

| Email | Password | Role |
|-------|----------|------|
| test@example.com | password123 | Owner |
| admin@example.com | admin123 | Admin |
| shelter@example.com | shelter123 | Shelter |
| john@example.com | password123 | Owner |
| sarah@example.com | password123 | Owner |

## 📱 Testing the App

1. **Login** with any test account
2. **Go to Discover** - You should see dogs with real photos
3. **Swipe** on dogs to test the matching system
4. **Create new dog** - Test photo upload functionality
5. **Check profile** - Verify user profile photos display correctly

## 🔍 Troubleshooting

### S3 Connection Issues
- Make sure AWS credentials are set in Render environment variables
- Check that the S3 bucket `dogmatch-bucket` exists and is accessible
- Verify the bucket region matches your configuration

### Photo Upload Issues
- Ensure sample images are in the correct directories
- Check file permissions and formats
- Verify the S3 service is properly initialized

### Database Issues
- The script automatically clears and recreates tables
- Make sure the backend is running and accessible
- Check Render logs for any errors

## 📝 Notes

- All sample images are from Unsplash (free to use)
- Images are automatically resized and optimized for the app
- The seeding script creates realistic test data for comprehensive testing
- S3 URLs are generated automatically and stored in the database

## 🎯 Next Steps

After successful seeding:
1. Test the swipe functionality in the app
2. Create new dogs and test photo uploads
3. Verify profile photos display correctly
4. Test event creation with photos (if implemented)
5. Check that all S3 URLs are working properly
