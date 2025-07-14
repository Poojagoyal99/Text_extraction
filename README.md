# 📝 Text Extraction from PDF/Image using OCR

This project provides a simple and effective way to extract text from **PDF** or **image** files using **OCR (Optical Character Recognition)**. It uses **Tesseract OCR** and **pdf2image** to process documents and output raw text.

## 📌 Features

- 📄 Convert PDFs to images using `pdf2image`.
- 🔍 Extract text from images using `pytesseract`.
-
- ## 🛠️ Requirements

- Python 3.x
- Tesseract OCR installed
- Poppler (for PDF to image conversion)
- Required Python packages

## 💾 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Poojagoyal99/Text_extraction.git
cd Text_extraction

###2. Set Up Virtual Environment (Optional but Recommended)
bash

python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows
pip install -r requirements.txt

Install Tesseract OCR
Windows:
Download and install from: https://github.com/tesseract-ocr/tesseract
(Add path to environment variables, usually: C:\Program Files\Tesseract-OCR\tesseract.exe)

Install Poppler for PDF conversion
Windows:
Download from: https://github.com/oschwartz10612/poppler-windows/releases
Extract and add the bin folder to your system PATH.
