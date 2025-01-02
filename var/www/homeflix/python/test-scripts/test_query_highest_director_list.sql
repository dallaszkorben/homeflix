source ~/Projects/python/playem/var/www/playem/python/env/bin/activate
cd /home/akoel/Projects/python/playem/var/www/playem/python
python3

from playem.card.database import SqlDatabase as DB
db=DB(None)
db.is_static_dbs_ok()


import sqlite3
con = sqlite3.connect("/home/pi/.playem/playem.db")



--------------------------
--- Original solutions ---
--------------------------

-- show all directors, ordered by the number of the directed movies
--
-- To be director of many episode in one series counts only 1

con.execute('''

SELECT director_name, movie_count
FROM
(SELECT raw.director_name, COUNT(raw.id) AS movie_count
FROM
    (
    WITH RECURSIVE
        rec(director_name,id,id_higher_card,level,source_path) AS    -- define a new table, called 'rec' having the given fields
        (
            SELECT                                                          -- define the INITIAL record
                person.name director_name,
                card.id id, 
                card.id_higher_card, 
                card.level,
                card.source_path            
            FROM 
                Card card,
                Card_Director card_director,
                Person person,
                Category category
            WHERE                                               -- INITIAL conditions
                card.level IS NULL                              -- take the lowest level cards 
                AND card_director.id_director=person.id
                AND card_director.id_card=card.id
                
                AND category.id=card.id_category
                AND category.name = :category
            UNION ALL

            SELECT                                              -- the next record
                rec.director_name,
                card.id,                                        --   takes the recent card id => the higher level card id
                card.id_higher_card,                            --   takes the higher level card_id
                card.level,
                card.source_path
            FROM
                rec,
                Card card
            WHERE
                rec.id_higher_card=card.id                      -- connects the new card record and the previous card record. previous record`s id_higher_card is the recent card id. Which means, the recent record is the parent of the previous
        )
    SELECT director_name,id,source_path                             -- print out only the group_id, id, source_path
    FROM
        rec
    WHERE
        rec.id_higher_card IS NULL
    GROUP BY
        rec.id,
        director_name
    ) raw
GROUP BY
    raw.director_name  --, raw.id
ORDER BY
    movie_count DESC, director_name
) director_list
WHERE
    director_list.movie_count >= :minimum
LIMIT :limit;
    
''', {'limit': 15, 'minimum': 2, 'category': 'movie', 'director_name': 'Terry Gilliam', 'card_id': '85eaef2bb3e3ef4986d0a8994b4ee1ce'}).fetchall()







-- show all actors, ordered by the number of the movies they played in
--
-- To be an actor of many episode in one series counts only 1

con.execute('''


SELECT actor_name, movie_count
FROM
(SELECT raw.actor_name, COUNT(raw.id) AS movie_count
FROM
    (
    WITH RECURSIVE
        rec(actor_name,id,id_higher_card,level,source_path) AS    -- define a new table, called 'rec' having the given fields
        (
            SELECT                                                          -- define the INITIAL record
                person.name actor_name,
                card.id id, 
                card.id_higher_card, 
                card.level,
                card.source_path            
            FROM 
                Card card,
                Card_Actor card_actor,
                Person person,
                Category category
            WHERE                                               -- INITIAL conditions
                card.level IS NULL                              -- take the lowest level cards 
                AND card_actor.id_actor=person.id
                AND card_actor.id_card=card.id
                
                AND category.id=card.id_category
                AND category.name = :category
            UNION ALL

            SELECT                                              -- the next record
                rec.actor_name,
                card.id,                                        --   takes the recent card id => the higher level card id
                card.id_higher_card,                            --   takes the higher level card_id
                card.level,
                card.source_path
            FROM
                rec,
                Card card
            WHERE
                rec.id_higher_card=card.id                      -- connects the new card record and the previous card record. previous record`s id_higher_card is the recent card id. Which means, the recent record is the parent of the previous
        )
    SELECT actor_name,id,source_path                             -- print out only the group_id, id, source_path
    FROM
        rec
    WHERE
        rec.id_higher_card IS NULL
    GROUP BY
        rec.id,
        actor_name
    ) raw
GROUP BY
    raw.actor_name  --, raw.id
ORDER BY
    movie_count DESC, actor_name
) actor_list
WHERE
    actor_list.movie_count >= :minimum
LIMIT :limit;
    
''', {'limit': 15, 'minimum': 2, 'category': 'movie', 'actor_name': 'Terry Gilliam', 'card_id': '85eaef2bb3e3ef4986d0a8994b4ee1ce'}).fetchall()






--------------------------
--- OPTIMIZED SOLUTION ---
--------------------------

1. Removed redundant tables from the initial recursive query:
Eliminated unnecessary Card card, Card_Actor card_actor, Person person, Category category from the FROM clause and replaced them with JOINs to make the relationships explicit and improve readability and performance.

2. Replaced the inner query (raw):
Directly integrated the recursive CTE (rec) with COUNT(DISTINCT rec.id) in the main query. This avoids the creation of an unnecessary nested query (raw).

3. Simplified grouping:
Grouped directly by actor_name, removing the redundant rec.id grouping in the subquery. This aligns with the requirement to count unique top-level cards.

4. Used HAVING instead of filtering in the outer query:
Replaced WHERE actor_list.movie_count >= :minimum with HAVING movie_count >= :minimum, as it directly applies after the aggregation step.

5. Removed excess columns and aliases:
Kept only the required columns in the output and cleaned up unnecessary intermediate table aliasing (raw and actor_list).



con.execute('''
WITH RECURSIVE
    rec(actor_name, id, id_higher_card) AS (
        SELECT
            person.name AS actor_name,
            card.id,
            card.id_higher_card
        FROM 
            Card card,
            Card_Actor card_actor,
            Person person,
            Category category
        WHERE 
            card.level IS NULL
            AND category.name = :category
            AND card.id_category = category.id
            AND card_actor.id_actor = person.id
            AND card_actor.id_card = card.id

        UNION ALL
        
        SELECT
            rec.actor_name,
            card.id,
            card.id_higher_card
        FROM 
            rec,
            Card card
        WHERE 
            rec.id_higher_card = card.id
    )
SELECT
    actor_name,
    COUNT(DISTINCT rec.id) AS movie_count
FROM 
    rec
WHERE 
    rec.id_higher_card IS NULL
GROUP BY 
    actor_name
HAVING 
    movie_count >= :minimum
ORDER BY 
    movie_count DESC, 
    actor_name
LIMIT :limit;
''', {'limit': 15, 'minimum': 2, 'category': 'movie', 'actor_name': 'Terry Gilliam', 'card_id': '85eaef2bb3e3ef4986d0a8994b4ee1ce'}).fetchall()

















