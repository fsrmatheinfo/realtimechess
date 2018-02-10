import aiohttp
import base64
import hashlib
import logging
import re

secret_key = b"Chess secret key that no one knows."

users = {}


class User:
	def __init__(self, name, password):
		self.id = name + "@anon.com"
		self.name = name
		self.password = password

	def __str__(self):
		return self.id


def password(name):
	sha256 = hashlib.sha256()
	sha256.update(name.encode("utf-8"))
	sha256.update(secret_key)
	return base64.b64encode(sha256.digest()).decode("ascii")


def get_current_user(request):
	name = request.cookies.get("name")
	if name is None:
		return None

	p = request.cookies.get("password")
	if p == password(name):
		return users.get(name, None)
	else:
		print("Incorrect password for " + name)
		return None


def authenticated(handler):
	def call_handler_if_ok(request):
		user = get_current_user(request)
		if user is None:
			aiohttp.web.HTTPForbidden(text="Not logged in.")
		return handler(request)

	return call_handler_if_ok


async def anonymous_login_handler(request):
	data = await request.post()
	print("LOGIN", data)
	name = data.get('name', None)
	if name is None:
		raise aiohttp.web.HTTPBadRequest(text="Need name.")
	destination = data.get("destination", None)
	if destination is None:
		destination = "/"

	# REquire A-Z for now.
	if len(name) > 20 or re.match("^[a-zA-Z0-9_-]+$", name) is None:
		raise aiohttp.web.HTTPBadRequest(text="Invalid name.")

	if name in users:
		pass
		# TODO: Forbid this.
		#raise aiohttp.web.HTTPUnauthorized(text="User already exists.")
	users[name] = User(name, password(name))

	print("Anonymous user: " + name)

	response = aiohttp.web.HTTPFound(destination)
	response.set_cookie('name', name, expires=None, path='/')
	response.set_cookie('password', password(name), expires=None, path='/')
	return response
