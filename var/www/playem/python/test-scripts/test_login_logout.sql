

!!! To send messages through curl, you have to use cookies with -c and -b switch !!!

# login and save the cookie
$ curl -c cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "username": "admin", "password": "admin"}' http://localhost:80/auth/login

# get the logged in user data - using the same cookie
$ curl -b cookies_1.txt --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request

# logout
curl -b cookies.txt --header "Content-Type: application/json" --request POST --data '{}' http://localhost:80/auth/logout



# try to restore the session
