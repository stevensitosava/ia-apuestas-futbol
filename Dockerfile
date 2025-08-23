FROM n8nio/n8n

USER root

RUN apk add --no-cache python3 py3-pip py3-pandas py3-requests py3-scipy

USER node