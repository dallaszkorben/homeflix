# playem
web media player


## Database 


```mermaid
erDiagram
    Card
    Theme
    MediaType
    Genre
    Language
    Text_Card_Language
    Country
    Hierarchy
    Category
    Medium
    Level
    Card_Theme }|--|| Card : id_card
    Card_Theme }|--|| Theme: id_theme
    Card_Mediatype
    Card_Genre
    Card_Sub
    Card_Sound
    Card_Origin
    Level_Title_Lang
```
