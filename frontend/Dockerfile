# Usamos uma imagem Node.js para construir nosso projeto
FROM node:18-alpine AS builder

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de definição de pacotes e instala as dependências
COPY package.json package-lock.json ./
RUN npm install

# Copia o resto do código-fonte do React
COPY . .

# Executa o comando de build para gerar os arquivos estáticos
RUN npm run build

# Usamos uma imagem Nginx super leve para servir os arquivos
FROM nginx:1.25-alpine

# Copia os arquivos estáticos construídos no estágio anterior para a pasta do Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Remove a configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia nossa própria configuração do Nginx
COPY nginx.conf /etc/nginx/conf.d

# Expõe a porta 80, que é a porta padrão do Nginx
EXPOSE 80

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]