import os
import hashlib
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image


class ImageSearchService:

    def __init__(self):

        # ==========================================
        # API configuration
        # ==========================================

        self.api_key = os.getenv("SERPER_API_KEY")

        self.search_url = os.getenv(
            "SERPER_IMAGE_SEARCH_URL",
            "https://google.serper.dev/images"
        )

        # ==========================================
        # Image configuration
        # ==========================================

        self.image_folder = Path(
            os.getenv(
                "IMAGE_FOLDER",
                "generated/images"
            )
        )

        self.image_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # Maximum number of search results
        self.max_results = int(
            os.getenv(
                "IMAGE_SEARCH_RESULTS",
                "10"
            )
        )

        # Minimum acceptable image dimensions
        self.min_width = int(
            os.getenv(
                "IMAGE_MIN_WIDTH",
                "640"
            )
        )

        self.min_height = int(
            os.getenv(
                "IMAGE_MIN_HEIGHT",
                "360"
            )
        )

        # HTTP timeout
        self.timeout = int(
            os.getenv(
                "IMAGE_DOWNLOAD_TIMEOUT",
                "20"
            )
        )

        # User-Agent
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0 Safari/537.36"
            )
        }

    # ==========================================================
    # PUBLIC METHOD
    # ==========================================================

    def search_and_download(
        self,
        query: str,
        filename: str | None = None
    ):
        """
        Search for a realistic image and download it.

        Returns:

        {
            "path": "...",
            "url": "...",
            "source": "...",
            "title": "...",
            "width": 1920,
            "height": 1080
        }
        """

        if not query or not query.strip():
            raise ValueError(
                "Image search query cannot be empty."
            )

        query = query.strip()

        print(
            f"[IMAGE] Searching for: {query}"
        )

        results = self.search_images(query)

        if not results:
            raise RuntimeError(
                f"No image results found for: {query}"
            )

        print(
            f"[IMAGE] Found {len(results)} results"
        )

        # ------------------------------------------------------
        # Try results one by one.
        #
        # Some image URLs returned by search engines can be:
        # - broken
        # - blocked
        # - HTML pages instead of images
        # - too small
        # ------------------------------------------------------

        for index, result in enumerate(
            results[:self.max_results],
            start=1
        ):

            image_url = result.get("imageUrl")

            if not image_url:
                continue

            print(
                f"[IMAGE] Trying result {index}: "
                f"{image_url}"
            )

            try:

                image_path = self.download_image(
                    image_url=image_url,
                    filename=filename
                )

                width, height = self.get_image_size(
                    image_path
                )

                # Check resolution
                if (
                    width < self.min_width
                    or
                    height < self.min_height
                ):

                    print(
                        f"[IMAGE] Image too small: "
                        f"{width}x{height}"
                    )

                    self.delete_file(image_path)

                    continue

                print(
                    f"[IMAGE] Selected: "
                    f"{width}x{height}"
                )

                return {
                    "path": str(image_path),
                    "url": image_url,
                    "source": result.get(
                        "source",
                        ""
                    ),
                    "title": result.get(
                        "title",
                        ""
                    ),
                    "width": width,
                    "height": height
                }

            except Exception as e:

                print(
                    f"[IMAGE] Failed result {index}: "
                    f"{type(e).__name__}: {e}"
                )

                continue

        raise RuntimeError(
            f"Could not download a valid image "
            f"for query: {query}"
        )

    # ==========================================================
    # IMAGE SEARCH
    # ==========================================================

    def search_images(self, query: str):
        """
        Search Google Images through Serper API.

        Returns a list of image results.
        """

        if not self.api_key:

            raise ValueError(
                "SERPER_API_KEY is not configured."
            )

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": self.max_results
        }

        try:

            response = requests.post(
                self.search_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

        except requests.exceptions.Timeout:

            raise TimeoutError(
                "Image search API request timed out."
            )

        except requests.exceptions.ConnectionError:

            raise ConnectionError(
                "Could not connect to image search API."
            )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "images",
            []
        )

        return results

    # ==========================================================
    # DOWNLOAD IMAGE
    # ==========================================================

    def download_image(
        self,
        image_url: str,
        filename: str | None = None
    ):
        """
        Download image URL to local storage.
        """

        if not image_url.startswith(
            ("http://", "https://")
        ):

            raise ValueError(
                "Invalid image URL."
            )

        # ------------------------------------------------------
        # Generate filename
        # ------------------------------------------------------

        if filename is None:

            filename = self.generate_filename(
                image_url
            )

        filename = self.sanitize_filename(
            filename
        )

        filepath = (
            self.image_folder /
            filename
        )

        # ------------------------------------------------------
        # Cache
        # ------------------------------------------------------

        if filepath.exists():

            print(
                f"[IMAGE] Using cached image: "
                f"{filepath}"
            )

            # Verify that cached file is valid
            try:

                self.validate_image(
                    filepath
                )

                return filepath

            except Exception:

                self.delete_file(
                    filepath
                )

        # ------------------------------------------------------
        # Download
        # ------------------------------------------------------

        try:

            response = requests.get(
                image_url,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )

        except requests.exceptions.Timeout:

            raise TimeoutError(
                "Image download timed out."
            )

        except requests.exceptions.ConnectionError:

            raise ConnectionError(
                "Could not connect to image URL."
            )

        response.raise_for_status()

        # ------------------------------------------------------
        # Check Content-Type
        # ------------------------------------------------------

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        # Some websites incorrectly report content-type,
        # so don't reject everything immediately.
        if (
            content_type
            and
            not content_type.startswith("image/")
            and
            "octet-stream" not in content_type
        ):

            print(
                f"[IMAGE] Warning: unexpected "
                f"Content-Type: {content_type}"
            )

        # ------------------------------------------------------
        # Save temporary file first
        # ------------------------------------------------------

        temp_filepath = filepath.with_suffix(
            ".tmp"
        )

        try:

            with open(
                temp_filepath,
                "wb"
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=8192
                ):

                    if chunk:
                        file.write(chunk)

            # --------------------------------------------------
            # Validate downloaded file
            # --------------------------------------------------

            self.validate_image(
                temp_filepath
            )

            # --------------------------------------------------
            # Convert to JPEG
            # --------------------------------------------------

            final_filepath = self.convert_to_jpeg(
                temp_filepath,
                filepath
            )

            self.delete_file(
                temp_filepath
            )

            return final_filepath

        except Exception:

            self.delete_file(
                temp_filepath
            )

            self.delete_file(
                filepath
            )

            raise

    # ==========================================================
    # VALIDATE IMAGE
    # ==========================================================

    def validate_image(
        self,
        filepath: Path
    ):
        """
        Check whether downloaded file is a valid image.
        """

        if not filepath.exists():

            raise FileNotFoundError(
                f"Image file does not exist: {filepath}"
            )

        if filepath.stat().st_size == 0:

            raise ValueError(
                "Downloaded image is empty."
            )

        try:

            with Image.open(filepath) as image:

                image.verify()

        except Exception as e:

            raise ValueError(
                f"Invalid image file: {e}"
            )

    # ==========================================================
    # GET IMAGE SIZE
    # ==========================================================

    def get_image_size(
        self,
        filepath: Path
    ):

        with Image.open(filepath) as image:

            return image.size

    # ==========================================================
    # CONVERT TO JPEG
    # ==========================================================

    def convert_to_jpeg(
        self,
        source_path: Path,
        destination_path: Path
    ):
        """
        Convert downloaded image to JPEG.

        This makes the image format consistent for
        PowerPoint/PIL processing.
        """

        try:

            with Image.open(source_path) as image:

                # ----------------------------------------------
                # Handle transparency
                # ----------------------------------------------

                if image.mode in (
                    "RGBA",
                    "LA",
                    "P"
                ):

                    background = Image.new(
                        "RGB",
                        image.size,
                        "white"
                    )

                    if image.mode == "P":
                        image = image.convert(
                            "RGBA"
                        )

                    background.paste(
                        image,
                        mask=image.getchannel("A")
                    )

                    image = background

                else:

                    image = image.convert(
                        "RGB"
                    )

                image.save(
                    destination_path,
                    "JPEG",
                    quality=95,
                    optimize=True
                )

        except Exception as e:

            raise ValueError(
                f"Could not convert image to JPEG: {e}"
            )

        return destination_path

    # ==========================================================
    # GENERATE FILENAME
    # ==========================================================

    def generate_filename(
        self,
        image_url: str
    ):

        parsed = urlparse(
            image_url
        )

        extension = (
            Path(
                parsed.path
            ).suffix.lower()
        )

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        }

        if extension not in allowed_extensions:

            extension = ".jpg"

        hash_value = hashlib.md5(
            image_url.encode(
                "utf-8"
            )
        ).hexdigest()[:12]

        return f"image_{hash_value}{extension}"

    # ==========================================================
    # SANITIZE FILENAME
    # ==========================================================

    def sanitize_filename(
        self,
        filename: str
    ):

        filename = Path(
            filename
        ).name

        # Prevent weird filenames
        filename = re_safe_filename(
            filename
        )

        # Always use .jpg because
        # downloaded images are converted to JPEG
        filename = Path(
            filename
        ).stem + ".jpg"

        return filename

    # ==========================================================
    # DELETE FILE
    # ==========================================================

    def delete_file(
        self,
        filepath
    ):

        try:

            filepath = Path(
                filepath
            )

            if filepath.exists():
                filepath.unlink()

        except Exception:

            pass


# ==============================================================
# SAFE FILENAME HELPER
# ==============================================================

def re_safe_filename(
    filename: str
):

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "_-."
    )

    result = ""

    for character in filename:

        if character in allowed:

            result += character

        else:

            result += "_"

    return result


# ==============================================================
# TEST
# ==============================================================

if __name__ == "__main__":

    from dotenv import load_dotenv

    load_dotenv()

    service = ImageSearchService()

    result = service.search_and_download(
        "Bangladesh rice field farmer agriculture"
    )

    print("\nIMAGE RESULT")
    print("-------------------------")

    print(
        "Path:",
        result["path"]
    )

    print(
        "URL:",
        result["url"]
    )

    print(
        "Source:",
        result["source"]
    )

    print(
        "Title:",
        result["title"]
    )

    print(
        "Size:",
        result["width"],
        "x",
        result["height"]
    )