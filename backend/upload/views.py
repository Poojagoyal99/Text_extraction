from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from PIL import Image
import pytesseract
import os

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        file_path = default_storage.save(file.name, file)
        full_path = default_storage.path(file_path)

        # OCR
        img = Image.open(full_path)
        extracted_text = pytesseract.image_to_string(img)

        return Response({"text": extracted_text})
