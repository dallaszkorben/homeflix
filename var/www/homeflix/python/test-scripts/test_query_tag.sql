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


res=con.execute('SELECT * FROM Tag WHERE tag.id_user=:user_id;', {'user_id': '1234'})
for hist in res.fetchall():
    print(hist)

or

con.execute('SELECT DISTINCT FROM Tag WHERE tag.id_user=:user_id;', {'user_id': '1234'}).fetchall()



#
# Insert into Tag table
#
con.execute('''
    INSERT INTO Tag (id_card, id_user, name)
        VALUES
            ('5583062bccde422e47378450068cc5a2', '1235', 'hello')
''') .fetchall()


# login
curl -c cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "username": "admin", "password": "admin"}' http://localhost:80/auth/login

# REST requests
curl -b cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "name": "my_tag"}' http://localhost:80/personal/tag/insert
curl -b cookies_1.txt --header "Content-Type: application/json" --request DELETE --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "name": "my_tag"}' http://localhost:80/personal/tag/delete
curl -b cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "card_id": "110a8be850ecda2ae99e4ddac5f8291f", "name": "my_tag1"}' http://localhost:80/personal/tag/insert

# fetch lowest level
curl -b cookies_1.txt --header "Content-Type: application/json" --request GET  http://localhost:80/collect/lowest/category/movie/view_state/*/level/*/genres/*/themes/*/directors/*/actors/*/lecturers/*/origins/*/decade/*/lang/en
curl -b cookies_1.txt --header "Content-Type: application/json" --request GET  http://localhost:80/collect/lowest/category/movie/view_state/interrupted/level/*/genres/*/themes/*/directors/*/actors/*/lecturers/*/origins/*/decade/*/lang/en
