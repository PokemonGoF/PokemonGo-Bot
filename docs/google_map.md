The webpage is a submodule to this repository and config related to that is in ./web folder

[OpenPoGoWeb](https://github.com/OpenPoGo/OpenPoGoWeb) uses Google Maps. Read their [README](https://github.com/OpenPoGo/OpenPoGoWeb/blob/master/README.md) for how to configure web frontend

## How to set up a simple webserver with nginx
## SimpleHTTPServer
You can either view the map via opening the html file, or by serving it with SimpleHTTPServer (runs on localhost:8000)
To use SimpleHTTPServer:
```
$ python -m SimpleHTTPServer [port]
```
The default port is 8000, you can change that by giving a port number. Anything above port 1000 does not require root.
You will need to set your username(s) in the userdata.js file before opening, **Copy userdata.js.example to userdata.js** and edit with your favorite text editor. Put your username in the quotes instead of "username"
If using multiple usernames format like this
```
var users = ["username1","username2"];
```
On Windows you can now go to http://127.0.0.1:8000 to see the map



### Nginx on Ubuntu 14.x, 16.x
#### 1. Install nginx on your Ubuntu machine (e.g. on locally or AWS)
```
sudo apt-get update
sudo apt-get install nginx
```

#### 2. Check the webserver
Check if the webserver is running by using your browser and entering the IP address of your local machine/server.
On a local machine this would be http://127.0.0.1. On AWS this is your public DNS if you haven't configured an elastic IP.

#### 3. Change Base Directory of the Webserver
```
sudo nano "/etc/nginx/sites-enabled/default"
```
Comment out following line: ```root /var/www/html;``` and change it to the web folder of your PokemonGo-Bot: eg:
```
/home/user/dev/PokemonGo-Bot/web;
```
Use `nginx -s reload` to load the new configurations.


***
Common Errors and Solutions

> missing  files: 127.0.0.1 - -  "GET /catchable-YOURACCOUNT.json 404
and location-SOMEACCOUNT.json 404

just create the file catachable-someaccount@gmail.com.json and put
```
{}
```
save and close repeat for other file. (location-SOMEACCOUNT.json)
