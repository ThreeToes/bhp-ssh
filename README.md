# bhp-ssh

"Reimagining" (read: overreengineered) of the SSH client and server from chapter
2 of Black Hat Python

## Installing
Initialise your Python environment using `virtualenv venv`, activate it with
`source venv/bin/activate` and then run `pip install -r requirements.txt` to 
install the dependencies

## Running

### Server
Run the server with 
`python bhp_ssh_server.py -o 127.0.0.1 -p 9000 -u user -a password`
to start a server on port 9000 using username `username` and password `password`

This will also leave a terminal open where shell commands can be typed to run
on the connecting clients

### Client
Run the client with 
`python bhp_ssh.py 127.0.0.1 9000 username password` to connect with the 
server spun up above. The client will run all commands sent to it and
return the output to the server