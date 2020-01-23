docker kill depot-python-app
docker build -t theresar/depot-python-app .
docker run -it -p 5000:5000 --rm theresar/depot-python-app