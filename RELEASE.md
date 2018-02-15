# Release && Deploy instructions

## Deploy to Docker Hub

```
# Set the environment, www or beta
export ENV=prod

# Before building the docker image, the i18n strings must be compiled
./scripts/compilemessages.py

# Build the docker image
docker build -t astrobin/astrobin -f docker/astrobin.dockerfile .
docker push astrobin/astrobin

# If you have changed the nginx configuration:
docker build --build-arg ENV=${ENV} -t astrobin/nginx -f docker/nginx.dockerfile .
docker push astrobin/nginx
```

