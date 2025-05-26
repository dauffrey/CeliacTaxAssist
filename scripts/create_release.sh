
#!/bin/bash

# Canadian Celiac Tax Calculator Release Script
# This script creates a Git tag and prepares for GitHub release

set -e

# Read version from VERSION file
VERSION=$(cat VERSION)
TAG="v$VERSION"

echo "🍁 Canadian Celiac Tax Calculator Release Creator"
echo "================================================"
echo "Creating release for version: $VERSION"
echo "Git tag: $TAG"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    echo "Please initialize git first:"
    echo "  git init"
    echo "  git add ."
    echo "  git commit -m 'Initial commit'"
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^$TAG$"; then
    echo "❌ Error: Tag $TAG already exists"
    echo "Please update the VERSION file with a new version number"
    exit 1
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "Commit them first? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "Prepare release $VERSION"
    else
        echo "❌ Please commit your changes first"
        exit 1
    fi
fi

# Create the tag
echo "📝 Creating Git tag $TAG..."
git tag -a "$TAG" -m "Release $VERSION

🍁 Canadian Celiac Tax Calculator v$VERSION

Major Features:
- Complete tax calculator for Canadian Celiac medical expenses
- OCR receipt scanning functionality  
- Multi-store price comparison database
- CRA-compliant tax credit calculations
- Multiple export formats (PDF, CSV, QIF, JSON)
- Secure user authentication system
- Full accessibility support (WCAG 2.1 AA)
- Mobile-responsive Canadian-themed design

Technical Highlights:
- Python 3.11+ with Streamlit framework
- PostgreSQL database with connection pooling
- Tesseract OCR with OpenCV image processing
- bcrypt password encryption
- Optimized for Replit deployment

For detailed changes, see CHANGELOG.md"

echo "✅ Tag $TAG created successfully!"
echo ""
echo "📋 Next Steps for GitHub Release:"
echo "1. Push the tag to GitHub:"
echo "   git push origin $TAG"
echo ""
echo "2. Go to GitHub and create a new release:"
echo "   - Navigate to your repository on GitHub"
echo "   - Click 'Releases' then 'Create a new release'"
echo "   - Select tag: $TAG"
echo "   - Title: 'Canadian Celiac Tax Calculator v$VERSION'"
echo "   - Copy the description from the tag message above"
echo "   - Attach any additional files if needed"
echo "   - Click 'Publish release'"
echo ""
echo "🎉 Release $VERSION ready for GitHub!"
