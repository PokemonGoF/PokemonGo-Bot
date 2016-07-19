# Pokemon Go API Demo

 * USE AT YOUR OWN RISK !
 * includes protobuf file
 * ugly code

## Demo

    $ python main.py -a "ptc" -u "username" -p "password" -l "New York, Washington Square"
    [!] Your given location: Washington Square, Greenwich, NY 12834, USA
    [!] lat/long/alt: 43.0909305 -73.4989367 0.0
    [!] PTC login for: sublimnl
    [+] RPC Session Token: TGT-842594-vsfLBEELnSrF ...
    [+] Received API endpoint: https://pgorelease.nianticlabs.com/plfe/94/rpc
    [+] Login successful
    [+] Username: username
    [+] You are playing Pokemon Go since: 2016-07-14 00:05:32
    [+] Poke Storage: 250
    [+] Item Storage: 350
    [+] POKECOIN: 0
    [+] STARDUST: 300

    $ python main.py -a "google" -u "gmail_account_username@gmail.com" -p "password" -l "New York, Washington Square"
    [!] Your given location: Washington Square, Greenwich, NY 12834, USA
    [!] lat/long/alt: 43.0909305 -73.4989367 0.0
    [!] Google login for: gmail_account_username@gmail.com
    [+] RPC Session Token: eyJhbGciOiJSUzI1NiIsImt ...
    [+] Received API endpoint: https://pgorelease.nianticlabs.com/plfe/490/rpc
    [+] Login successful
    [+] Username: <nickname>
    [+] You are playing Pokemon Go since: 2016-07-12 20:59:39
    [+] Poke Storage: 250
    [+] Item Storage: 350
    [+] POKECOIN: 0
    [+] STARDUST: 100

## Creating a config file
Copy config.json.example in config.json and update accordingly eg:

    {
        "auth_service": "google",
        "username": "example@gmail.com",
        "password": "password11!!",
        "location": "New York",
        "debug": true,
        "client_secret": "000000000000000000"
    }

## Credits
Thanks a lot to [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the inspiration and parts of the code!  
[C# Port](https://github.com/BclEx/pokemongo-api-demo.net) by BclEx !  
[Node Port](https://github.com/Armax/Poke.io) by Arm4x  
Thanks a lot to [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
