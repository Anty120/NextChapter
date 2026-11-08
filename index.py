"""Python-compatible WSGI entry; Django preset resolves the same application."""

from nextchapter.wsgi import application

app = application
