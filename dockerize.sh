
#!/bin/bash

docker build -t vtg_km .
docker image tag vtg_km coxphl1/vtg_km:1.7
docker push coxphl1/vtg_km:1.7
