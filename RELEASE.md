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
```

