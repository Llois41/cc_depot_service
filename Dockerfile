FROM python:alpine3.7
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV FLASK_ENV="production"
# EXPOSE 3003
# ENTRYPOINT [ "python" ]
CMD [ "python", "depot.py", "flask", "run", "--host", "0.0.0.0"]