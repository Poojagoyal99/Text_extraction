"""
Module for extracting content from PDF files.

This file contains the class for extracting content from PDF files.

Classes:
    PDFExtractor: The class for extracting content from PDF files.
"""

import base64
import json
from typing import Any, Dict, List

import fitz  # PyMuPDF
from loguru import logger
from unstructured.partition.pdf import partition_pdf

class PDFExtractor(BaseExtractor):
    """
    Class for extracting content from PDF files.

    Methods:
        extract_text(file_path: str) -> str: Extracts the text from a PDF file.
    """

    def __init__(
        self,
        ai_client: AIClient,
        prompt_manager: PromptManager,
    ) -> None:
        """Initialize the ImageExtractor with Anthropic client and prompt manager."""
        super().__init__()
        self.ai_client = ai_client
        self.prompt_manager = prompt_manager

    def _extract_images_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        images = []
        pdf_document = fitz.open(pdf_path)

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]

            # First method: Get images as is
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    base64_data = base64.b64encode(image_bytes).decode("utf-8")

                    images.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": f"image/{image_ext}",
                                "data": base64_data,
                            },
                            "page_num": page_num + 1,
                            "image_num": img_index + 1,
                        },
                    )

                except Exception as e:
                    logger.warning(
                        f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - Failed to process image {img_index} on page {page_num}: {e!s}",
                    )
        pdf_document.close()
        return images

    async def _process_image_with_claude(self, image_data: Dict[str, Any]) -> str:
        if not self.ai_client:
            return f"[Claude API not configured for image on page {image_data['page_num']}]"

        try:
            # Create a clean image object with only the required fields
            image_for_api = {
                "type": "image",
                "source": image_data["source"],
            }

            # Get prompt from prompt manager
            prompt = self.prompt_manager.get_prompt(PromptName.IMAGE_EXTRACTION)
            if prompt is None:
                logger.warning(
                    f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - Failed to get image extraction prompt",
                )
                return None

            content = [image_for_api, {"type": "text", "text": prompt}]

            message = await self.ai_client.generate_response(
                prompt=content,
                model=ClaudeModel.CLAUDE_3_7_SONNET,
                max_tokens=8192,
            )

            if not message or not message.content:
                return f"[No response received for image on page {image_data['page_num']}]"

            return message.content[0].text
        except Exception as e:
            logger.info(
                f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - Failed to process image with Claude: {e!s}",
            )
            return f"[Failed to process image on page {image_data['page_num']}]"

    async def extract(self, file_path: str) -> ExtractorTaskOutputWithMetadata:
        """
        Extracts the text from a PDF file.

        Arguments:
            file_path {str} -- The path to the PDF file.

        Returns:
            ExtractorTaskOutputWithMetadata -- The extracted text from the PDF file.
        """
        logger.debug(
            f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - Extracting text from PDF file: {file_path}",
        )
        try:
            # Extract text content
            partitioned_elements = partition_pdf(file_path, strategy="fast")
            text_content = "\n".join(
                [el.text for el in partitioned_elements if el.text],
            )

            # Process images and track failures
            images = self._extract_images_from_pdf(file_path)
            successful_extractions = []
            failed_extractions = []
            image_descriptions = []

            for img in images:
                try:
                    result = await self._process_image_with_claude(img)
                    if result:
                        successful_extractions.append(
                            {
                                "page": img["page_num"],
                                "image_num": img["image_num"],
                            },
                        )
                        image_descriptions.append(
                            f"[Image on page {img['page_num']}: {result}]",
                        )
                    else:
                        error_msg = "Claude processing failed"
                        failed_extractions.append(
                            {
                                "page": img["page_num"],
                                "image_num": img["image_num"],
                                "reason": error_msg,
                            },
                        )
                except Exception as e:
                    error_msg = str(e)
                    failed_extractions.append(
                        {
                            "page": img["page_num"],
                            "image_num": img["image_num"],
                            "reason": error_msg,
                        },
                    )

            # Log detailed extraction statistics
            total_images = len(images)
            success_count = len(successful_extractions)
            failure_count = len(failed_extractions)

            logger.info(
                f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - PDF Processing Statistics:\n"
                f"File: {file_path}\n"
                f"Total Images: {total_images}\n"
                f"Successfully Processed: {success_count}\n"
                f"Failed Processing: {failure_count}\n"
                f"Success Rate: {(success_count / total_images) * 100 if total_images > 0 else 0:.2f}%",
            )

            if failed_extractions:
                logger.warning(
                    f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - Failed Image Extractions:\n"
                    f"File: {file_path}\n"
                    f"Failed Images: {json.dumps(failed_extractions, indent=2)}",
                )

            # Combine text and image content
            full_content = text_content
            if image_descriptions:
                full_content += "\n\nEmbedded Images:\n" + "\n".join(image_descriptions)

            logger.info(
                f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - "
                f"Final extracted content from PDF {file_path}:\n{full_content}",
            )
            return ExtractorTaskOutputWithMetadata(
                content=full_content,
                metadata={},
            )

        except Exception as e:
            logger.error(
                f"{RoutingKeys.MEDIA_PROCESSING_EXTRACTOR_TASK} - Failed to process PDF: {e!s}",
            )
            raise MediaProcessingException(
                error=e,
                message="Failed to process the PDF file.",
            ) from e
