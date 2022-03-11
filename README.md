# ionos-ddns-docker
1&amp;1 Ionos DDNS Client with Docker Container Buildfile

**Example docker-compose:**

```
version: '3.6'
services: 
  ionos-ddns:
    container_name: ionos-ddns
    build:
      context: /docker/data/ionos
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - CHECK_INTERVAL=200
      - HOSTNAMES=domain1.de, domain2.de, domain3.de
      - PREFIX=<your-api-prefix>
      - KEY=<your-api-key>
      - DESCRIPTION=DDNS Updater
      - API_URL=https://api.hosting.ionos.com/dns/v1/dyndns
      - PUBLIC_IP_URL=https://ident.me
```

You may need to change the build context directory! The build folder should contain the *ionos.py* and the *Dockerfile*.

**Environment Variables:**

`CHECK_INTERVAL` - Defines update check interval in seconds. Default is *180*<br>

`HOSTNAMES` - Hostnames that you want to get updated. Seperated with comma.<br>

`PREFIX` - Your API Key Prefix. You have to get the key prefix from Ionos.<br>

`KEY` - Your API Key. You have to get the key from Ionos.<br>

`DESCRIPTION` - Description of you API call, for exmaple *DDNS Update*.<br>

`API_URL` - Ionos API URL, default is *https://api.hosting.ionos.com/dns/v1/dyndns*.<br>

`PUBLIC_IP_URL` - API URL to get public IP address, default is *https://ident.me*.
