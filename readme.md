El codigo intenta procesar una 'request' proveniente de la skill y devolver una 'response' acorde. Pasea el objeto que recibe buscando el tipo de consulta que se esta haciendo para resolver el tipo de respuesta. 

- Obligatoriamente debe existir una directiva dentro del request. 

- namespace: Interfaz a la que se le hace la request. 
- name: Accion dentro de la interfaz

Se crea un objeto AlexaResponse para armar una respuesta para alexa usando el formato esperado. 

Interfaces: 
    - Authorization.AcceptGrant: Va a llegar al handler de lambda cuando un usuario esta haciendo Account Linking o cuando un usuario quiere usar un spa. Puede que llegue un authorization code o un access token. test: AcceptGrant_Directive
    
    Se debe ubicar el token dentro del payload de la directiva y usarlo para negociar con el servidor web. En caso de no tener token se debe enviar un codigo de autorizacion. 
    - Discovery:


## Testing
    
Dependencies:
    - nose2
    - pytest

Run tests:
    Standing in parent dir, run ```pytest```