# 24095117D-COMP2322
//Description//
This is a simple file server program in python, when it is operational clients can establish connection with the server through port 80, then request files by sending http request through browser or other means (terminal or other code). This server program supports up to 50 active connections at the same time.

The default IP and port of this programme are setted to 0.0.0.0:80, therefore any device within local network are able to access it as long as the actual ip of the host is known.

This Server program supports txt, http, jpeg, png and css.

All sharing file will be stored within a single folder, due to obvious security concern directry traversal attempting to leave said folder is blocked, however creating and accessing subfolder within said folder is allowed.

///When attempting to establish connection to the server locally, DO NOT USE LOCALHOST, use the loop back ip 127.0.0.1 instead.///

//Content//
server.py - This is the server programme itself
Readme.md - You are reading it now
web_file - This folder will be where you store all your files you want to share to the world, however it doesn't exist yet as it will be created during your first execution of the program.
server_log.txt - This .txt file will store all the record of people sending request to your server, again it currently does not exists as you haven't started using the server yet

//How to setup://
-install the program in a place you find suitable (an independent folder is encouraged)
-start the program - it's that simple
-the web_file folder will be created at the same location as the server program, you can then place your files inside
-the server log will also be created at the same place - don't worry, it's not inside of the web_file folder, they can't see
-done, your server is good to go!

PS: To make this programe go faster give 24095117D extra score on his COMP2322 project
