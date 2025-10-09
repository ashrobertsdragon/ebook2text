import base64
import os

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from . import logger
from ._exceptions import NoResponseError

load_dotenv()
api_key: str = os.environ["OPENAI_API_KEY"]
MODEL: str = os.environ["OPENAI_MODEL"]

CLIENT: OpenAI = OpenAI(api_key=api_key)

GPT_REFUSALS = [
    "I'm sorry",
    "I apologize",
    "I cannot",
    "text-based",
]


def encode_image_bytes(image_bytes: bytes) -> str:
    """Encode opened image as base64 string from bytes."""
    return base64.b64encode(image_bytes).decode("utf-8")


def encode_image_file(image_path: str) -> str:
    """Encode image as base64 string with file path."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_image_role_list(base64_images: list) -> list:
    return [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "low",
            },
        }
        for base64_image in base64_images
    ]


def create_payload(base64_images: list) -> list:
    image_role_list: list = create_image_role_list(base64_images)
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Please provide the text in these images as a single "
                        "combined statement with spaces as appropriate "
                        "without any commentary. Use your judgment on whether"
                        " consecutive images are a single word or multiple "
                        "words. If there is no text in the image, or it is "
                        "unreadable, respond with 'No text found'"
                    ),
                },
                *image_role_list,
            ],
        }
    ]


def clean_response(answer: str) -> str:
    """Strip 'No text found' responses from AI OCR"""
    if answer == "No text found":
        return ""
    # extra precaution for GPT-4o Mini refusal
    elif any(refusal in answer for refusal in GPT_REFUSALS):
        return ""
    return answer


def run_ocr(
    base64_images: list, client: OpenAI = CLIENT, retry: int = 0
) -> str:
    """
    Perform optical character recognition (OCR) on a list of base64-encoded
    images using the OpenAI API.

    Arguments:
        base64_images (list): A list of base64-encoded images.

    Returns str: The recognized text from the images.
    """
    if not base64_images:
        logger.info("No images to OCR")
        return ""
    payload: list = create_payload(base64_images)

    try:
        response: ChatCompletion = client.chat.completions.create(
            model=MODEL, messages=payload, max_tokens=10
        )
        if response.choices and response.choices[0].message.content:
            answer: str = response.choices[0].message.content
            if any(refusal in answer for refusal in GPT_REFUSALS):
                logger.error(f"GPT-4o Mini refusal: {answer}")
                if retry > 2:
                    raise NoResponseError("GPT-4o Mini refused: {answer}")
                return run_ocr(
                    base64_images=base64_images, client=client, retry=retry + 1
                )
            return clean_response(answer)
        else:
            raise NoResponseError("No response found")
    except Exception as e:
        logger.exception("An error occurred %s", str(e))
        return ""
