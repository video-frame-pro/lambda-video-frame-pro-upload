import boto3
import json
import logging
import os
import urllib.request
import urllib.error

# Inicialização de clientes AWS
s3_client = boto3.client('s3')

# Variáveis
BUCKET_NAME = os.environ["BUCKET_NAME"]
VIDEO_CONTENT_TYPE = "video/mp4"
MAX_FILE_SIZE_MB = 100

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_response(status_code, message=None, data=None):
    """
    Gera uma resposta formatada.
    """
    response = {"statusCode": status_code, "body": {}}
    if message:
        response["body"]["message"] = message
    if data:
        response["body"].update(data)
    return response

def normalize_body(event):
    """
    Normaliza o corpo da requisição para garantir que seja um dicionário.
    """
    if isinstance(event.get("body"), str):
        return json.loads(event["body"])  # Desserializa string JSON para dicionário
    elif isinstance(event.get("body"), dict):
        return event["body"]  # Já está em formato de dicionário
    else:
        raise ValueError("Request body is missing or invalid.")

def validate_request(body):
    """
    Valida os campos obrigatórios na requisição.
    """
    required_fields = ["video_id", "user_name", "video_url", "email"]
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_video_url(video_url):
    """
    Valida o link do vídeo verificando sua acessibilidade, tamanho e tipo de conteúdo.
    """
    try:
        logger.info(f"Validating video link: {video_url}")
        request = urllib.request.Request(video_url, method="HEAD")  # Usamos HEAD para evitar baixar o conteúdo inteiro
        response = urllib.request.urlopen(request)

        if response.status != 200:
            raise ValueError("The URL is invalid or inaccessible.")

        # Obtém o tamanho do arquivo
        content_length = int(response.headers.get("Content-Length", 0))

        # Verifica se o tamanho do arquivo é maior que zero (se o arquivo não está vazio)
        if content_length == 0:
            raise ValueError("The file is empty.")

        # Verifica se o tamanho do arquivo está dentro do limite
        if content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"The file size exceeds the {MAX_FILE_SIZE_MB}MB limit.")

        # Valida se o tipo de conteúdo da resposta é vídeo MP4
        content_type = response.headers.get("Content-Type", "")
        if content_type != VIDEO_CONTENT_TYPE:
            raise ValueError(f"Invalid content type: {content_type}. Expected {VIDEO_CONTENT_TYPE}.")

        logger.info("Video link validated successfully.")
    except urllib.error.URLError as e:
        logger.error(f"Failed to validate video link: {e}")
        raise ValueError(f"Failed to validate the video link: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during video link validation: {e}")
        raise ValueError(f"Unexpected error during video link validation: {str(e)}")

def download_video(video_url):
    """
    Faz o download do vídeo a partir do link fornecido.
    """
    try:
        logger.info(f"Downloading video from: {video_url}")
        request = urllib.request.Request(video_url)

        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                logger.info("Video downloaded successfully.")
                return response.read()
            else:
                raise ValueError(f"Failed to download video. HTTP status code: {response.status}")

    except urllib.error.URLError as e:
        logger.error(f"Failed to download video: {e}")
        raise ValueError(f"Failed to download the video: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during video download: {e}")
        raise ValueError(f"Unexpected error during video download: {str(e)}")

def upload_video_to_s3(video_content, user_name, process_id):
    """
    Faz o upload do vídeo baixado para o bucket S3.
    """
    try:
        video_key = f"videos/{user_name}/{process_id}/upload/{process_id}-source.mp4"
        logger.info(f"Uploading video to S3 bucket: {BUCKET_NAME}, key: {video_key}")
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=video_key,
            Body=video_content,
            ContentType=VIDEO_CONTENT_TYPE
        )
        logger.info("Video uploaded to S3 successfully.")
        return video_key
    except Exception as e:
        logger.error(f"Error uploading video to S3: {e}")
        raise ValueError(f"Failed to upload video to S3: {str(e)}")

def lambda_handler(event, context):
    """
    Entrada principal da Lambda.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Normaliza o corpo da requisição
        body = normalize_body(event)

        # Valida os campos obrigatórios na requisição
        validate_request(body)

        # Extrai os dados da requisição
        user_name = body["user_name"]
        email = body["email"]
        video_id = body["video_id"]
        video_url = body["video_url"]

        logger.info(f"Processing video upload for user: {user_name}, video_id: {video_id}")

        # Valida o link do vídeo
        validate_video_url(video_url)

        # Faz o download do vídeo
        video_content = download_video(video_url)

        # Faz o upload do vídeo para o S3
        video_key = upload_video_to_s3(video_content, user_name, video_id)

        # Retorna a resposta de sucesso
        return create_response(
            200,
            data={
                "user_name": user_name,
                "email": email,
                "video_id": video_id,
                "video_url": video_url
            }
        )
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return create_response(400, message=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_response(500, message="An unexpected error occurred. Please try again later.")
