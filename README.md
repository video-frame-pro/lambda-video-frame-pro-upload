# lambda-video-frame-pro-upload

Este repositório implementa o endpoint de **upload** de vídeos. Os vídeos são enviados pelo usuário para o **API Gateway**, que os armazena no **S3**.

## Funções
- Implementar o endpoint **/upload** para enviar vídeos.
- Integrar o **API Gateway** com o **S3** para armazenar os vídeos.

## Tecnologias
- AWS API Gateway
- AWS S3

## Como usar
1. Configure o **API Gateway** para aceitar uploads de vídeos.
2. Armazene os vídeos no **S3**.
3. Proteja o endpoint com autenticação JWT via **Cognito**.
