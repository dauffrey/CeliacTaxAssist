
# Changelog

All notable changes to the Canadian Celiac Tax Calculator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-28

### Added
- Complete Canadian Celiac Tax Calculator web application
- User authentication system with secure password hashing
- Product tracking for gluten-free vs regular price comparisons
- OCR-powered receipt scanning functionality
- Price comparison database across multiple stores
- Tax credit calculations following CRA guidelines
- Multiple export formats (PDF, CSV, QIF, JSON)
- Educational content with CRA guidelines
- Interactive chat assistant for tax-related questions
- Accessibility features (WCAG 2.1 AA compliant)
- Mobile-responsive design
- Canadian-themed branding and styling

### Features
- **Core Functionality**
  - Product management with price tracking
  - Receipt scanning with OCR text extraction
  - Store price comparison system
  - Automated tax credit calculations
  - Multi-format data export capabilities

- **Advanced Features**
  - Secure user authentication
  - PostgreSQL database with connection pooling
  - Educational CRA guidelines integration
  - Interactive chat assistant
  - Full accessibility support
  - Mobile-optimized interface

- **Technical Stack**
  - Python 3.11+ with Streamlit framework
  - PostgreSQL database backend
  - Tesseract OCR with OpenCV image processing
  - ReportLab PDF generation
  - bcrypt password encryption
  - Optimized for Replit deployment

### Security
- bcrypt password hashing
- Secure session management
- Input validation and sanitization
- User data isolation by account
- HTTPS-ready deployment configuration

### Accessibility
- WCAG 2.1 AA compliance
- Full keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Skip navigation links
- Proper ARIA labels and semantic HTML

[1.0.0]: https://github.com/yourusername/canadian-celiac-tax-calculator/releases/tag/v1.0.0
