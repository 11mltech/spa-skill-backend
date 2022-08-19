El codigo intenta procesar una 'request' proveniente de la skill y devolver una 'response' acorde. Pasea el objeto que recibe buscando el tipo de consulta que se esta haciendo para resolver el tipo de respuesta. 

- Obligatoriamente debe existir una directiva dentro del request. 
- namespace: Interfaz a la que se le hace la request. 
- name: Accion dentro de la interfaz

Se crea un objeto AlexaResponse para armar una respuesta para alexa usando el formato esperado. 

### Implemented interfaces

- Alexa.Authorization, AcceptGrant
- Alexa.Discovery, Discover
- Alexa.ToggleController: TurnOn, TurnOff
- Alexa.TemperatureController: tbd

### Implemented Instances
    - ToggleController: Spa.Lights, Spa.Jets
    - TemperatureController: Spa.Temp


## Testing

1. miniconda installation:
https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html#

2. once miniconda is installed and you are in base environment, create a new one:

    `conda create --name <env>`

    `conda activate --name <env>`


3. Install dependencies for testing:

    `conda install pytest`

    `conda install -c conda-forge bottle`


4. Stand in root directory and run

    `pytest`

## Deploy test-server.py on milonet


1. ssh to milonet

    `$ ssh username@milonet.duckdns.org`

2. clone repo (create ssh keys with [ssh-keygen](https://docs.github.com/es/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) if necessary)
3. Install python 3.8, if not installed already, and dependencies (bottle and pytest)
4. Set nginx to listen to port 3434 and assign route /spa
5. run server and test it with curl from another terminal
    
    `curl -kvvv https://milonet.duckdns.org/spa/discovery/0101`
6. Copy test/spa-test-server.service file into /etc/systemd/system/spa-test-server.service
7. Start/stop/restart the service:

    `sudo systemctl start spa-test-server`

    `sudo systemctl stop spa-test-server`

    `sudo systemctl restart spa-test-server`

Restart with every new update from remote. 