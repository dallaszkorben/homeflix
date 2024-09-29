#
# start python
#
# cd /var/www/playem/python
$ source /var/www/playem/python/env/bin/activate
$ python3


#
# intitialization
#
import sqlite3
from playem.card.database import SqlDatabase as DB
db=DB(None)
con = sqlite3.connect("/home/akoel/.playem/playem.db")

#
# DB requests:
#
con.execute('SELECT * FROM User;').fetchall()
con.execute('SELECT * FROM History;').fetchall()
con.execute('SELECT * FROM Rating;').fetchall()
con.execute('SELECT card.* FROM Card, Text_Card_Lang tcl WHERE tcl.id_card=card.id AND tcl.type="T" AND tcl.text LIKE "%2001%";').fetchone()

#
# Reset dbs
#
con.execute('DROP TABLE History;').fetchall()
con.execute('DROP TABLE Rating;').fetchall()
db.recreate_personal_dbs()
db.recreate_static_dbs()
 
#
# feth ROWID for every table which has autoincrement:
#
con.execute('''
    select * from sqlite_sequence
''', {'lang': 'hu'}).fetchall()


#
# Fetch all db:
#
res = con.execute("SELECT name FROM sqlite_master WHERE type='table';")
for name in res.fetchall():
    print(name[0])
    
#
# Fetch history of a user:
#
con.execute('''
SELECT *
FROM
    User as user,
    History as history,
    Language as lang
WHERE
    history.id_user=user.id
    AND user.id_language=lang.id
    AND user.id=:user_id;
''', {'user_id': '1234'}).fetchall()

#
# Fetch history of a media of a user
# print the records in separate lines
#
res = con.execute('SELECT datetime(start_epoch, "unixepoch", "localtime"), last_position FROM History WHERE id_card=:id_card ORDER BY start_epoch;',{'id_card': 'a842968e01a203e1efe295001d837ca6'})
for rec in res.fetchall():
    print(rec)

res = con.execute('SELECT datetime(start_epoch, "unixepoch", "localtime"), last_position FROM History WHERE id_card=:id_card ORDER BY start_epoch;',{'id_card': '067243a51521181250adb9fb52b5adb5'})
for rec in res.fetchall():
    print(rec)

#
# Get the latest history
#
curl  --header "Content-Type: application/json" --request GET --data '{ "user_id": 1234, "card_id": "067243a51521181250adb9fb52b5adb5", "limit_records": 1}' http://localhost:80/personal/history/request
    


#
# Add one movie to History of a user
#
# id: 5583062bccde422e47378450068cc5a2      -> 2001 space Odyssey card 
# id: 82d634cd47562844409e749b02871dc0      -> Lucy
#

# start a new history for a card
curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1234, "card_id": "5583062bccde422e47378450068cc5a2", "last_position": "0:00:12"}' http://localhost:80/personal/history/update
1727528344

# add new history to an existing history - use the start_epoch from the previous request
# curl  --header "Content-Type: application/json" --request POST http://localhost:80/personal/history/update/by/user_id/1234/card_id/5583062bccde422e47378450068cc5a2/last_position/0:00:15/start_epoch/1727528344
# curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1234, "card_id": "5583062bccde422e47378450068cc5a2", "last_position": "0:00:19", "start_epoch": 1727528344}' http://localhost:80/personal/history/update

