# Release && Deploy instructions

## Deploy to Hyper.sh

```
# Set the environment, www or beta
export ENV=www

# Before building the docker image, the i18n strings must be compiled
./scripts/compilemessages.py

# Build the docker image
docker build -t astrobin/astrobin -f docker/astrobin.dockerfile .

# Push it
docker push astrobin/astrobin

# Stop containers that depend on this image on Hyper.sh
hyper stop astrobin celery && hyper rm astrobin celery

# Remove the image
hyper rmi astrobin/astrobin

# Stop nginx too or Hyper will ask to claim another FIP
hyper stop nginx && hyper rm nginx

# Start again
hyper compose up -d -f hyper-compose.yml astrobin celery nginx
```
