#
# start python
#
#cd /var/www/homeflix/python
#source /var/www/homeflix/python/env/bin/activate
#sudo -u pi python3
sudo -u pi bash -c "cd /var/www/homeflix/python && source /var/www/homeflix/python/env/bin/activate && python3"



#
# intitialization
#
import sqlite3
from homeflix.card.database import SqlDatabase as DB
db=DB(None)
#con = sqlite3.connect(db.db_path)
#con = db.conn
con = sqlite3.connect("/home/pi/.homeflix/homeflix.db")
con.execute('PRAGMA journal_mode=DELETE')
con.execute('PRAGMA synchronous=OFF')
con.row_factory = None

#
# DB requests:
#
con.execute('SELECT * FROM Search;').fetchall()
con.execute('SELECT * FROM Search_Request;').fetchall()
con.execute('SELECT * FROM Search_Data_Field;').fetchall()
con.execute('SELECT * FROM Search search, Search_Request sr, Search_Data_Field sdf WHERE sdf.id_search=search.id AND search.id_search_request=sr.id;').fetchall()

--- show the data belonging to a specific Search
con.execute('''
    SELECT
        sdf.name,
        sdf.value
    FROM
        Search_Data_Field sdf,
        Search s
    WHERE
        sdf.id_search = s.id
        AND s.id = :search_id
    ;''', {'search_id': 1}) .fetchall()

--- collect Search records in 1 line (data will be concatenated)
con.execute('''
SELECT
    s.id,
    s.thumbnail_id,
    s.title,
    sr.id_request_method,
    sr.id_request_protocol,
    sr.id_request_path,
    GROUP_CONCAT(sdf.name || '=' || sdf.value, '|') as data
FROM
    Search s
    JOIN Search_Request sr ON s.id_search_request = sr.id
    LEFT JOIN Search_Data_Field sdf ON s.id = sdf.id_search
WHERE
    s.id_user = :user_id
    AND s.thumbnail_id = :thumbnail_id
GROUP BY
    s.id, s.thumbnail_id, s.title, sr.id_request_method, sr.id_request_protocol, sr.id_request_path;''',
{'user_id': 0, 'thumbnail_id': 'movie_search'}) .fetchall()


#
# Reset dbs
#
con.execute('DROP TABLE Search_Data_Field;').fetchall()
con.execute('DROP TABLE Search;').fetchall()
con.execute('DROP TABLE Search_Request;').fetchall()

con.execute('DROP TABLE Request_Method;').fetchall()
con.execute('DROP TABLE Request_Protocol;').fetchall()
con.execute('DROP TABLE Request_Path;').fetchall()
db.recreate_personal_dbs()
db.recreate_static_dbs()

#
# Create new Search with direct database commands
#

# Insert request components
con.execute('INSERT OR IGNORE INTO Request_Method (name) VALUES (?)', ('GET',))
con.execute('INSERT OR IGNORE INTO Request_Protocol (name) VALUES (?)', ('http',))
con.execute('INSERT OR IGNORE INTO Request_Path (name) VALUES (?)', ('/collect/highest/mixed',))
con.execute('INSERT OR IGNORE INTO Request_Path (name) VALUES (?)', ('/collect/lowes/',))

# Insert search request
search_request_id = con.execute('''
    INSERT INTO Search_Request (
        id_request_method,
        id_request_protocol,
        id_request_path)
    VALUES (?, ?, ?)
    RETURNING id''',
    ('GET', 'http', '/collect/highest/mixed')).fetchone()[0]

# Insert search record
search_id = con.execute('''
    INSERT INTO Search (
        thumbnail_id,
        title,
        id_search_request,
        id_user)
    VALUES (?, ?, ?, ?)
    RETURNING id''',
    ('movie search 2', 'movie search 2', search_request_id, 1)).fetchone()[0]

# Insert search data fields
con.execute('INSERT INTO Search_Data_Field (id_search, name, value) VALUES (?, ?, ?)', (search_id, 'category', 'movie'))
con.execute('''
    INSERT INTO Search_Data_Field (
        id_search,
        name,
        value
    ) VALUES (?, ?, ?)
    ''', (1, 'genre', 'action'))

con.commit()
print(f"Search created with id: {search_id}")


----------------------------------------------------

# Login
curl -c cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "username": "admin", "password": "admin"}' http://192.168.0.21/auth/login

# Get personal search settings
curl  -b cookies_1.txt --header "Content-Type: application/json" --data '{"thumbnail_id":"movie_search"}' --request GET http://192.168.0.21/personal/search/get