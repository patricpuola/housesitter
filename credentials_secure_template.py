#!/usr/bin/python3

# After you have filled all the credentials, rename this file to credentials_secure.py

class Cred(object):
	def __init__(self):
		self.username = None
		self.password = None
		self.api_key = None

opencage = Cred()
opencage.username = "username"
opencage.password = "password"
opencage.api_key = "apikey"
