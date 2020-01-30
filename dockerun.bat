docker kill depotapp
docker build -t theresar/depot-python-app .
docker run -it -p 5000:5000 --rm --name depotapp  theresar/depot-python-app
docker run -it --rm -d --name mongodb -p 27018:27017 -v mongodbdate:/data/db mongo:latest