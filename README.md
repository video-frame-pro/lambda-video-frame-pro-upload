<p align="center">
  <img src="https://i.ibb.co/zs1zcs3/Video-Frame.png" width="30%" />
</p>

---

Este repositório contém a implementação da **lógica de upload de vídeos** do sistema **Video Frame Pro**, responsável por validar, baixar e enviar os vídeos para o Amazon S3.

---

## Função

A função Lambda realiza as seguintes operações:

1. **Validação do Link**: Verifica se o link fornecido aponta para um vídeo válido (formato MP4 e tamanho aceitável).
2. **Download do Vídeo**: Faz o download do vídeo a partir do link fornecido.
3. **Upload para o S3**: Envia o vídeo para um bucket S3 configurado.

---

## Campos da Requisição

A função Lambda espera um evento com os seguintes campos:

- **video_id** (obrigatório): Identificador único do vídeo.
- **user_name** (obrigatório): Nome do usuário que está enviando o vídeo.
- **video_url** (obrigatório): URL do vídeo a ser processado.
- **email** (obrigatório): E-mail do usuário.

### Exemplo de Entrada

#### Upload de Vídeo

```json
{
   "body": {
     "user_name": "usuario123",
     "email": "usuario@email.com",
     "video_id": "12345",
     "video_url": "https://example.com/video.mp4"
   }
}
```

---

## Exemplos de Resposta

### Sucesso

```json
{
  "statusCode": 200,
  "body": {
    "user_name": "usuario123",
    "email": "usuario@email.com",
    "video_id": "12345",
    "video_url": "https://example.com/video.mp4"
  } 
}
```

### Erro de Validação

```json
{
  "statusCode": 400,
  "body": {
    "message": "Validation failed."
  }
}
```

### Erro Interno

```json
{
  "statusCode": 500,
  "body": {
    "message": "An unexpected error occurred. Please try again later."
  }
}
```

---

## Tecnologias

<p>
  <img src="https://img.shields.io/badge/AWS-232F3E?logo=amazonaws&logoColor=white" alt="AWS" />
  <img src="https://img.shields.io/badge/AWS_Lambda-4B5A2F?logo=aws-lambda&logoColor=white" alt="AWS Lambda" />
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/GitHub-ACTION-2088FF?logo=github-actions&logoColor=white" alt="GitHub Actions" />
</p>

---

## Estrutura do Repositório

```
/src
├── upload
│   ├── upload.py         # Lógica de upload de vídeos
│   ├── requirements.txt  # Dependências do Python
│   ├── __init__.py       # Inicialização do pacote
/tests
├── upload
│   ├── upload_test.py    # Testes unitários para a função de upload de vídeos
│   ├── requirements.txt  # Dependências do Python para testes
│   ├── __init__.py       # Inicialização do pacote para testes
/infra
├── main.tf               # Definição dos recursos AWS com Terraform
├── outputs.tf            # Outputs das funções e recursos Terraform
├── variables.tf          # Definições de variáveis Terraform
├── terraform.tfvars      # Arquivo com variáveis de ambiente
```

---

## Passos para Configuração

### Pré-Requisitos

1. Configure as credenciais da AWS.
2. Certifique-se de que o bucket S3 já esteja criado e configurado.

### Deploy da Infraestrutura

1. No diretório `infra`, configure o arquivo `terraform.tfvars` com as variáveis necessárias.
2. Execute o Terraform:

```bash
cd infra
terraform init
terraform apply -auto-approve
```

---

### Testes Unitários

1. Rode o bloco para instalar as dependências de testes, executar os testes e gerar o relatório de cobertura:

```sh
find tests -name 'requirements.txt' -exec pip install -r {} +
pip install coverage coverage-badge
coverage run -m unittest discover -s tests -p '*_test.py'
coverage report -m
coverage html
```

---

## Licença

Este projeto está licenciado sob a **MIT License**. Consulte o arquivo LICENSE para mais detalhes.

---

Desenvolvido com ❤️ pela equipe Video Frame Pro.
