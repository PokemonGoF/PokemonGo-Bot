Start by downloading for your platform: [Mac](https://www.docker.com/products/docker#/mac), [Windows](https://www.docker.com/products/docker#/windows), or [Linux](https://www.docker.com/products/docker#/linux). Once you have Docker installed, simply create the various config.json files for your different accounts (e.g. `configs/config-account1.json`) and then create a Docker image for PokemonGo-Bot using the Dockerfile in this [repo](https://hub.docker.com/r/svlentink/pokemongo-bot/).

#Automatic setup
Use this docker hub url: https://hub.docker.com/r/svlentink/pokemongo-bot/
```
docker pull svlentink/pokemongo-bot
```

#Manual setup
```
cd PokemonGo-Bot
docker build -t pokemongo-bot .
```
You can verify that the image was created with:
```
docker images
```

To run PokemonGo-Bot Docker image you've created, simple run:
```
docker run --name=pokego-bot1 --rm -it -v $(pwd)/configs/config-account1.json:/usr/src/app/configs/config.json pokemongo-bot
```
_Check the logs in real-time `docker logs -f pgobot`_

If you want to run multiple accounts with the same Docker image, simply specify different config.json and names in the Docker run command.
Do not push your image to a registry with your config.json and account details in it!

Share web folder with host:
```
docker run -it -v $(pwd)/web/:/usr/src/app/web --rm --name=pgo-bot-acct1 pokemongo-bot --config config.json
```

TODO: Add configuration for running multiple Docker containers from the same image for every bot instance, and a single container for the web UI.
