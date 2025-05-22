# Usa uma imagem oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o container
COPY . /app

# Instala as dependências
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe a porta que o Flask usará
EXPOSE 10000

# Variável de ambiente para garantir que o Flask rode em produção
ENV FLASK_ENV=production

# Comando para rodar o app
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
