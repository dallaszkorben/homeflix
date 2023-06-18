# playem
web media player


## Solutions
###1. Using the Flask, every second time whey I tried to create a new cursor (self.conn.cursor) to send SQL query, an error message appeared:
```sh
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 140499707700800 and this is thread id 140499674129984.
```
It did not happen when I ran the code individually.
Reason: The database connection was created in a different thead than the connection was used.
The connection was created in the main thread, but it was used in the @route, which is a new thread
Solution: I the sqlite3 API (https://docs.python.org/3/library/sqlite3.html#sqlite3.connect) you can find a parameter for the "connect()" method:
*check_same_thread (bool) – If True (default), ProgrammingError will be raised if the database connection is used by a thread other than the one that created it. If False, the connection may be accessed in multiple threads; write operations may need to be serialized by the user to avoid data corruption. See threadsafety for more information.*
```sh
self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
```


