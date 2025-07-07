from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UploadedFile  # 👈 import your model
from .serializers import FileUploadSerializer  # 👈 create this
from django.core.files.storage import default_storage
from PIL import Image
import pytesseract
import os

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    # def get(self, request):
    #     files = UploadedFile.objects.all().order_by('-uploaded_at')
    #     serializer = FileUploadSerializer(files, many=True)
    #     return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)
        
        # ✅ Check supported extensions
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in valid_extensions:
            return Response({"error": "Unsupported file format."}, status=400)

        # Save file to database
        uploaded = UploadedFile.objects.create(file=file)

        # OCR
        full_path = uploaded.file.path
        img = Image.open(full_path)
        extracted_text = pytesseract.image_to_string(img)

        return Response({
            "text": extracted_text,
            "file": uploaded.file.url  # ⬅️ send file URL back to frontend
        })
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from PIL import Image
import pytesseract
import os
from pdf2image import convert_from_path

# Set Tesseract path (change if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set Poppler path (point to your poppler bin folder)
POPPLER_PATH = r"C:\Users\Pooja\Downloads\poppler-23.11.0\Library\bin"  # Change if your path is different

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        ext = os.path.splitext(file.name)[1].lower()
        valid_image_ext = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        valid_pdf_ext = ['.pdf']

        file_path = default_storage.save(file.name, file)
        full_path = default_storage.path(file_path)

        try:
            if ext in valid_image_ext:
                img = Image.open(full_path)
                text = pytesseract.image_to_string(img)

            elif ext in valid_pdf_ext:
                images = convert_from_path(full_path, poppler_path=POPPLER_PATH)
                text = ""
                for img in images:
                    text += pytesseract.image_to_string(img) + "\n"

            else:
                return Response({"error": "Unsupported file format"}, status=400)

            return Response({"text": text.strip()})
        
        except Exception as e:
            return Response({"error": str(e)}, status=500)
