
# 🍁 Canadian Celiac Tax Calculator

A comprehensive web application designed to help Canadians with Celiac Disease track and calculate medical expense tax credits for gluten-free products according to CRA guidelines.

## 🎯 Features

### Core Functionality
- **Product Tracking**: Add and manage gluten-free products with price comparisons
- **Receipt Scanner**: OCR-powered receipt scanning to automatically extract product prices
- **Price Comparison Database**: Track prices across different stores and locations
- **Tax Calculations**: Automatic calculation of eligible medical expense tax credits
- **Multi-format Export**: Generate reports in PDF, CSV, QIF, and JSON formats

### Advanced Features
- **User Authentication**: Secure user accounts with encrypted password storage
- **Educational Content**: Built-in CRA guidelines and filing information
- **Chat Assistant**: Interactive help system for tax-related questions
- **Accessibility**: Full keyboard navigation and screen reader support
- **Mobile Responsive**: Optimized for desktop and mobile devices

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Git (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/canadian-celiac-tax-calculator.git
   cd canadian-celiac-tax-calculator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run main.py
   ```

4. **Access the app**
   Open your browser and navigate to `http://localhost:5000`

### Running on Replit
This project is optimized for Replit deployment:
1. Import the repository into Replit
2. Click the "Run" button
3. The application will automatically start on port 5000

## 📊 Usage Guide

### 1. Getting Started
- Create an account or log in
- Navigate through the tabs to access different features

### 2. Adding Products
- Use the "Products" tab to manually add gluten-free items
- Enter both gluten-free and regular product prices
- Include store information and purchase dates

### 3. Scanning Receipts
- Upload receipt images in the "Scan Receipt" tab
- The OCR system will automatically detect items and prices
- Review and categorize detected items as gluten-free or regular

### 4. Price Comparison
- Build a database of prices across different stores
- Find the best deals for gluten-free products
- Track price trends over time

### 5. Generating Tax Reports
- View your tax summary in the "Summary" tab
- Export data in multiple formats for tax software
- Download CRA-compliant PDF reports

## 🏗️ Project Structure

```
├── components/          # UI components
│   ├── auth.py         # Authentication system
│   ├── chat_assistant.py # Interactive help system
│   ├── educational_content.py # CRA guidelines
│   ├── price_comparison.py # Store price tracking
│   ├── product_form.py # Product entry forms
│   ├── product_list.py # Product display
│   └── receipt_scanner.py # OCR functionality
├── database/           # Database management
│   └── db_manager.py   # PostgreSQL operations
├── utils/              # Utility functions
│   ├── calculations.py # Tax credit calculations
│   ├── ocr_processor.py # Image processing
│   ├── pdf_generator.py # Report generation
│   └── tax_export.py   # Data export formats
├── assets/             # Static files
│   └── styles.css      # Custom CSS styling
├── .streamlit/         # Streamlit configuration
└── main.py            # Application entry point
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.11
- **Database**: PostgreSQL with connection pooling
- **OCR**: Tesseract OCR with OpenCV
- **Authentication**: bcrypt with secure session management
- **PDF Generation**: ReportLab
- **Image Processing**: PIL (Pillow) and OpenCV
- **Deployment**: Optimized for Replit hosting

## 📋 Dependencies

Key packages include:
- `streamlit>=1.39.0` - Web application framework
- `pytesseract>=0.3.13` - OCR functionality
- `opencv-python>=4.10.0.84` - Image processing
- `psycopg2-binary>=2.9.10` - PostgreSQL connectivity
- `reportlab>=4.2.5` - PDF generation
- `bcrypt>=4.2.0` - Password encryption
- `pillow>=10.4.0` - Image handling

See `pyproject.toml` for complete dependency list.

## 💰 CRA Compliance

This application follows Canada Revenue Agency guidelines for medical expense claims:

### Eligible Expenses
- Incremental cost of gluten-free products over regular alternatives
- Products must be medically necessary for Celiac Disease
- Requires medical practitioner certification

### Documentation Requirements
- Medical diagnosis of Celiac Disease
- Receipts for gluten-free products
- Price comparisons with regular products
- Annual summary of incremental costs

### Tax Credit Calculation
- Federal tax credit rate: 15% of eligible expenses
- Expenses must exceed the lesser of $2,421 or 3% of net income
- Provincial credits may also apply

## 🔒 Security & Privacy

- **Secure Authentication**: bcrypt password hashing
- **Session Management**: Secure session tokens
- **Data Privacy**: User data isolated by account
- **Input Validation**: Comprehensive input sanitization
- **HTTPS Ready**: SSL/TLS support for production deployment

## ♿ Accessibility

- **WCAG 2.1 AA Compliant**: Meets accessibility standards
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Friendly**: Proper ARIA labels and semantic HTML
- **High Contrast**: Accessible color schemes
- **Mobile Responsive**: Touch-friendly interface

## 🚀 Deployment

### Replit Deployment (Recommended)
1. Import project to Replit
2. Configure environment variables if needed
3. Use the built-in deployment system
4. Application automatically scales and manages SSL

### Manual Deployment
```bash
# Set environment variables
export DATABASE_URL="your_postgresql_url"

# Run with production settings
streamlit run main.py --server.port 5000 --server.address 0.0.0.0
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [CRA Medical Expenses Guide](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/lines-33099-33199-eligible-medical-expenses-you-claim-on-your-tax-return.html)
- **Issues**: Report bugs or request features via GitHub Issues
- **Email**: support@example.com

## 🙏 Acknowledgments

- Canada Revenue Agency for medical expense guidelines
- Celiac Canada for advocacy and awareness
- Tesseract OCR team for open-source OCR technology
- Streamlit team for the excellent web framework

---

**Made in Canada 🍁 for the Celiac Community**

*This application is not affiliated with the Canada Revenue Agency. Always consult with a tax professional for official tax advice.*
