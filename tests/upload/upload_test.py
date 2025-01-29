import json
import os
import urllib.error
from unittest import TestCase
from unittest.mock import patch, MagicMock
from botocore.exceptions import BotoCoreError

os.environ["BUCKET_NAME"] = "mocked-bucket"

from src.upload.upload import (
    lambda_handler,
    validate_video_link,
    download_video,
    upload_video_to_s3,
    validate_request,
    normalize_body
)


class TestLambdaFunction(TestCase):

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_validate_video_link_success(self, mock_urlopen):
        """Teste de sucesso para validação do link do vídeo."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "video/mp4", "Content-Length": "1024"}
        mock_urlopen.return_value = mock_response

        try:
            validate_video_link("http://valid-url.com/video.mp4")
        except Exception as e:
            self.fail(f"validate_video_link raised an exception unexpectedly: {e}")

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_validate_video_link_invalid_content_type(self, mock_urlopen):
        """Teste para erro de tipo de conteúdo inválido."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/pdf", "Content-Length": "1024"}
        mock_urlopen.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            validate_video_link("http://valid-url.com/file.pdf")

        self.assertIn("Invalid content type", str(context.exception))

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_validate_video_link_file_too_large(self, mock_urlopen):
        """Teste para erro de arquivo maior que o limite permitido."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "video/mp4", "Content-Length": str(200 * 1024 * 1024)}
        mock_urlopen.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            validate_video_link("http://valid-url.com/largefile.mp4")

        self.assertIn("The file size exceeds", str(context.exception))

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_validate_video_link_http_403(self, mock_urlopen):
        """Teste para erro HTTP 403 durante a validação do link do vídeo."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://restricted-url.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None
        )

        with self.assertRaises(ValueError) as context:
            validate_video_link("http://restricted-url.com")

        self.assertIn("Failed to validate the video link: HTTP Error 403", str(context.exception))

    ## ------------------------------- ##
    ## Testes para download_video()     ##
    ## ------------------------------- ##

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_download_video_success(self, mock_urlopen):
        """Teste de sucesso para o download do vídeo."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"video content"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        content = download_video("http://valid-url.com/video.mp4")

        self.assertEqual(content, b"video content")

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_download_video_failure(self, mock_urlopen):
        """Teste para falha no download do vídeo."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://invalid-url.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None
        )

        with self.assertRaises(ValueError) as context:
            download_video("http://invalid-url.com")

        self.assertIn("Failed to download the video", str(context.exception))

    ## --------------------------------- ##
    ## Testes para lambda_handler()      ##
    ## --------------------------------- ##

    @patch("src.upload.upload.upload_video_to_s3")
    @patch("src.upload.upload.download_video")
    @patch("src.upload.upload.validate_video_link")
    def test_lambda_handler_success(self, mock_validate_video_link, mock_download_video, mock_upload_video_to_s3):
        """Teste de sucesso para o fluxo completo da Lambda."""
        event = {
            "body": json.dumps({
                "video_id": "123",
                "user_name": "testuser",
                "video_url": "http://valid-url.com/video.mp4",
                "email": "testuser@example.com"
            })
        }
        context = {}

        mock_validate_video_link.return_value = True
        mock_download_video.return_value = b"video content"
        mock_upload_video_to_s3.return_value = "videos/testuser/123/upload/123-source.mp4"

        response = lambda_handler(event, context)
        response_body = response["body"]

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response_body["user_name"], "testuser")
        self.assertEqual(response_body["email"], "testuser@example.com")
        self.assertEqual(response_body["video_id"], "123")
        self.assertEqual(response_body["video_url"], "http://valid-url.com/video.mp4")


    @patch("src.upload.upload.urllib.request.urlopen")
    def test_lambda_handler_download_error(self, mock_urlopen):
        """Teste para erro no download do vídeo."""
        event = {
            "body": json.dumps({
                "video_id": "123",
                "user_name": "testuser",
                "video_url": "http://invalid-url.com",
                "email": "testuser@example.com"
            })
        }
        context = {}

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://invalid-url.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None
        )

        response = lambda_handler(event, context)
        response_body = response["body"]

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Failed to validate the video link: HTTP Error 403", response_body["message"])

        ## ----------------------------- ##
    ## Testes para normalize_body()  ##
    ## ----------------------------- ##

    def test_normalize_body_valid_dict(self):
        """Teste para corpo da requisição já em formato de dicionário."""
        event = {"body": {"video_id": "123"}}
        self.assertEqual(normalize_body(event), {"video_id": "123"})

    def test_normalize_body_valid_json_string(self):
        """Teste para corpo da requisição como string JSON válida."""
        event = {"body": json.dumps({"video_id": "123"})}
        self.assertEqual(normalize_body(event), {"video_id": "123"})

    def test_normalize_body_invalid_body(self):
        """Teste para erro ao tentar normalizar um corpo inválido."""
        event = {"body": 123}  # Corpo inválido (não é string nem dicionário)
        with self.assertRaises(ValueError) as context:
            normalize_body(event)
        self.assertIn("Request body is missing or invalid.", str(context.exception))

    ## ----------------------------- ##
    ## Testes para validate_request() ##
    ## ----------------------------- ##

    def test_validate_request_success(self):
        """Teste para validação de requisição válida."""
        body = {"video_id": "123", "user_name": "testuser", "video_url": "http://valid-url.com/video.mp4", "email": "test@example.com"}
        try:
            validate_request(body)
        except Exception as e:
            self.fail(f"validate_request raised an exception unexpectedly: {e}")

    def test_validate_request_missing_fields(self):
        """Teste para erro de campos obrigatórios ausentes."""
        body = {"video_id": "123", "user_name": "testuser"}
        with self.assertRaises(ValueError) as context:
            validate_request(body)
        self.assertIn("Missing required fields: video_url, email", str(context.exception))


        ## ----------------------------- ##
    ## Testes para validate_request() ##
    ## ----------------------------- ##

    def test_validate_request_success(self):
        """Teste para validação de requisição válida."""
        body = {"video_id": "123", "user_name": "testuser", "video_url": "http://valid-url.com/video.mp4", "email": "test@example.com"}
        try:
            validate_request(body)
        except Exception as e:
            self.fail(f"validate_request raised an exception unexpectedly: {e}")

    def test_validate_request_missing_fields(self):
        """Teste para erro de campos obrigatórios ausentes."""
        body = {"video_id": "123", "user_name": "testuser"}
        with self.assertRaises(ValueError) as context:
            validate_request(body)
        self.assertIn("Missing required fields: video_url, email", str(context.exception))

    ## ----------------------------- ##
    ## Testes para validate_video_link() ##
    ## ----------------------------- ##

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_validate_video_link_http_error(self, mock_urlopen):
        """Teste para erro HTTP durante a validação do link do vídeo."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://restricted-url.com",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None
        )

        with self.assertRaises(ValueError) as context:
            validate_video_link("http://restricted-url.com")

        self.assertIn("Failed to validate the video link: HTTP Error 403", str(context.exception))

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_validate_video_link_unexpected_error(self, mock_urlopen):
        """Teste para erro inesperado durante a validação do link."""
        mock_urlopen.side_effect = Exception("Unexpected error")

        with self.assertRaises(ValueError) as context:
            validate_video_link("http://error-url.com")

        self.assertIn("Unexpected error during video link validation", str(context.exception))

    ## ----------------------------- ##
    ## Testes para download_video() ##
    ## ----------------------------- ##

    @patch("src.upload.upload.urllib.request.urlopen")
    def test_download_video_unexpected_error(self, mock_urlopen):
        """Teste para erro inesperado durante o download do vídeo."""
        mock_urlopen.side_effect = Exception("Unexpected error")

        with self.assertRaises(ValueError) as context:
            download_video("http://error-url.com")

        self.assertIn("Unexpected error during video download", str(context.exception))

    ## ----------------------------- ##
    ## Testes para upload_video_to_s3() ##
    ## ----------------------------- ##

    @patch("src.upload.upload.s3_client.put_object")
    def test_upload_video_to_s3_success(self, mock_put_object):
        """Teste de sucesso para upload do vídeo no S3."""
        mock_put_object.return_value = None
        video_key = upload_video_to_s3(b"video content", "testuser", "123")
        self.assertEqual(video_key, "videos/testuser/123/upload/123-source.mp4")

    @patch("src.upload.upload.s3_client.put_object")
    def test_upload_video_to_s3_failure(self, mock_put_object):
        """Teste para erro ao tentar fazer upload do vídeo para o S3."""
        mock_put_object.side_effect = BotoCoreError()

        with self.assertRaises(ValueError) as context:
            upload_video_to_s3(b"video content", "testuser", "123")

        self.assertIn("Failed to upload video to S3", str(context.exception))

    ## ----------------------------- ##
    ## Testes para lambda_handler() ##
    ## ----------------------------- ##

    @patch("src.upload.upload.upload_video_to_s3")
    @patch("src.upload.upload.download_video")
    @patch("src.upload.upload.validate_video_link")
    def test_lambda_handler_unexpected_error(self, mock_validate_video_link, mock_download_video, mock_upload_video_to_s3):
        """Teste para erro inesperado na lambda_handler."""
        event = {
            "body": json.dumps({
                "video_id": "123",
                "user_name": "testuser",
                "video_url": "http://valid-url.com/video.mp4",
                "email": "testuser@example.com"
            })
        }
        context = {}

        mock_validate_video_link.return_value = True
        mock_download_video.return_value = b"video content"
        mock_upload_video_to_s3.side_effect = Exception("Unexpected error")

        response = lambda_handler(event, context)
        response_body = response["body"]

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("An unexpected error occurred", response_body["message"])
