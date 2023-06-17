# playem
web media player


## Database 


```mermaid
erDiagram
    Card {
        int id
        String length
        String date
        String source_path
    }
    Card_Theme {
        int id_card
        int id_theme
        String name
    }

    Card_Genre {
        int id_card
        int id_genre
        String name
    }

    Medium {
        String name
        int id_card
    }

    MediaType
    Genre
    Text_Card_Language
    Country
    Hierarchy
    Category
    Level

    Card_Theme }|--|| Card : id_card
    Card_Theme }|--|| Theme: id_theme

    Card_Genre }|--|| Card: id_card
    Card_Genre }|--|| Genre: id_genre

    Card_Origin }|--|| Card: id_card
    Card_Origin }|--|| Country: id_origin

    Medium }|--|| Card: id_card

    Card }|--|| Language: id_title_orig

    Card_Mediatype
    Card_Sub
    Card_Sound
    Card_Origin
    Level_Title_Lang
```
