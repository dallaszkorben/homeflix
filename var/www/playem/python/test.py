#!env/bin/python

from playem.config.config import Config

config = Config()
print(config.getLogLevel())
print(config.getLogFileName())
print(config.getWebRelativePath())
print(config.getWebAbsolutePath())
print(config.getMediaAbsolutePath())
