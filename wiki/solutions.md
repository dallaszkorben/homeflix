# Solutions
## 1. Using the Flask, every second time whey I tried to create a new cursor (self.conn.cursor) to send SQL query, an error message appeared:
```sh
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 140499707700800 and this is thread id 140499674129984.
```
It did not happen when I ran the code individually.

Reason: The database connection was created in a different thead than the connection was used.

The connection was created in the main thread, but it was used in the @route, which is a new thread

Solution: I the sqlite3 API (https://docs.python.org/3/library/sqlite3.html#sqlite3.connect) you can find a parameter for the "connect()" method:

*check_same_thread (bool) – If True (default), ProgrammingError will be raised if the database connection is used by a thread other than the one that created it. If False, the connection may be accessed in multiple threads; write operations may need to be serialized by the user to avoid data corruption. See threadsafety for more information.* 
```python
self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
```


## 2. Collect SQL query rows into one row:

The Card table with the given Card.id has an n:m relation to Genre table through the Card_Genre Table.
That means a query for a Card with Genre will give back as many lines as many Genre the Card has.
But we want only one hit, and all the Genre should be collected in one field separated with comma
```python
>>> import sqlite3
>>> con = sqlite3.connect("/home/akoel/.playem/playem.db")
>>> con.execute('''
...                 SELECT group_concat(genre.name) as genres
...                 FROM 
...                     Genre genre,
...                     Card_Genre card_genre
...                 WHERE 
...                     card_genre.id_card = :card_id AND
...                     genre.id = card_genre.id_genre
... ''', {'card_id': 4}).fetchone()
('adventure,drama,horror',)
```



## 3. Media selector:

HTML:
```javascript
<body>
    <div id="thumbnail-sections" tabindex="0">
        <div id="section-0" class="thumbnail-section">
            <div class="thumbnail-container" id="section-0_container-0">
                <div class="thumbnail" id="section-0_container-0_thumbnail-0">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">First box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
                <div class="thumbnail" id="section-0_container-0_thumbnail-1">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">Second box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
                <div class="thumbnail" id="section-0_container-0_thumbnail-2">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">Third box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
                <div class="thumbnail" id="section-0_container-0_thumbnail-3">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">Fourth box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
                <div class="thumbnail" id="section-0_container-0_thumbnail-3">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">Fifth box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
                <div class="thumbnail" id="section-0_container-0_thumbnail-3">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">Sixth box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
                <div class="thumbnail" id="section-0_container-0_thumbnail-3">
                    <div class="thumbnail-text-wrapper">
                        <div class="thumbnail-text">Seventh box</div>
                    </div>
                    <img src="images/categories/movie.jpg" alt="Image">
                </div>
            </div>
        </div>
    </div>
    <div id="left-arrow"><</div>
    <div id="right-arrow">></div>
</body>
```

CSS:
```javascript
.thumbnail-section {
    box-sizing:border-box;      /* element and padding and border are included in the width and height */
    height: 40%;                /* occupies the upper 40% of the browser's screen. if you chnage the browser's height, it changes */
    width: 100%;                /* occupies the whole browser sceen horizontally */
    display: flex;              /* flex box layout model */
    flex-direction: column;     /* stacks the flex items vertically */
    flex-wrap: nowrap;          /* the flex items will not wrap */
    overflow: hidden;           /* flex items which does not fit, will be hidden */
    border: 1px red solid;
    background-color: rgb(205, 212, 19);
}

.thumbnail-container {
    box-sizing:border-box;      /* element and padding and border are included in the width and height */
    height: 250px;              /* fix height of the container */
    min-height: 250px;          /* it must be set. ??? */
    width: 100%;                /* it occupies the whole .thumbnail-section horizontally */
    display: flex;              /* flex box layout model */
    flex-direction: row;        /* stacks the flex items vertically */
    flex-wrap: nowrap;          /* the flex items will not wrap */
    overflow: hidden;           /* flex items which does not fit, will be hidden */
    border: 1px blue solid;
    background-color: rgb(77, 77, 77);
}

.thumbnail {
    box-sizing:border-box;      /* element and padding and border are included in the width and height */
    height: 100%;               /* occupies the full height of the .thumbnail-container */       
    margin-right: 5px;
    margin-left: 5px;

    border: 5px solid transparent; /* for the focus frame */
    background-color: rgb(35, 140, 135);

    display: flex;              /* flex box layout model */
    position: relative;          /* This made the animation with text work. I do not know how */
}

.thumbnail img {
    width: 300px;
    height: 238px;              /* .thumbnail-container height:300px -1px border -2x5px .thumbnail border */
    max-height: 238px;
    object-fit: contain;        /* resize the image: keeps aspect ratio, resize to fit to the dimesion */
}

.thumbnail-text-wrapper{            
    position: absolute;         /* relative to the neares positioned ancestor: .thumbnail. That is the reason the .thumbnail has position: relative */
    max-width: 300px;           /* needed to tell to the absolute positioned element what is the size otherwise the 'absolute' element does not know*/
    width: 300px;               /* needed to tell to the absolute positioned element what is the size otherwise the 'absolute' element does not know*/
    height: 238px;              /* needed to tell to the absolute positioned element what is the size otherwise the 'absolute' element does not know*/
    max-height: 238px;          /* needed to tell to the absolute positioned element what is the size otherwise the 'absolute' element does not know*/

    font-family: 'Brush Script MT', cursive;
    font-weight: bold;
    font-size: 70px;
    color: rgb(70, 26, 231);
    text-shadow: 
        -1px -1px 0px black,
        1px -1px 0px black,
        1px 1px 0px black,
        -1px 1px 0px black;
}

.thumbnail-text{                /* needed to centralize horizontally the text*/
    position: relative;
    text-align: center;         /* the .thumbail-text-wrapper has position:absolute, so it is not possible to align to center */
}

#left-arrow,
#right-arrow {
    cursor: pointer;
    font-size: 24px;
    margin-top: 5px;
}

#left-arrow {
    margin-right: 10px;
}
```

jQuery
```javascript
$(document).ready(function() {
    var thumbnails = $('.thumbnail');
    var currentIndex = 0;
          
    // first thumbnail is selected by default
    thumbnails.eq(currentIndex).css('border-color', 'red');
          
    $('#right-arrow').click(function() {
        thumbnails.eq(currentIndex).css('border-color', 'transparent');
        currentIndex = (currentIndex + 1) % thumbnails.length;
        thumbnails.eq(currentIndex).css('border-color', 'red');
        scrollThumbnails();
    });
          
    $('#left-arrow').click(function() {
        thumbnails.eq(currentIndex).css('border-color', 'transparent');
        currentIndex = (currentIndex - 1 + thumbnails.length) % thumbnails.length;
        thumbnails.eq(currentIndex).css('border-color', 'red');
        scrollThumbnails();
    });

    function scrollThumbnails() {
        var container = $('.thumbnail-container');
        var thumbnailWidth = thumbnails.eq(0).outerWidth(true);
        var containerWidth = container.width();
        var containerScrollLeft = container.scrollLeft();
        var visibleThumbnails = Math.floor(containerWidth / thumbnailWidth);

        if (currentIndex >= visibleThumbnails + containerScrollLeft / thumbnailWidth) {
            container.animate({ scrollLeft: thumbnailWidth * (currentIndex - visibleThumbnails + 1) }, 200);
        } else if (currentIndex < containerScrollLeft / thumbnailWidth) {
            container.animate({ scrollLeft: thumbnailWidth * currentIndex }, 200);
        }
    }
});
```

## 4. Show and fit image to a DIV background while keep the aspect ratio:
The idea was the following:

CSS:
```javascript
<style>
    #detail-image-div{
        height: 100%;
        width: 50%;

        background: url(MEDIA/01.Movie/01.Standalone/A.Kenguru-1976/image.jpg);*/
        background-position: right top;
        background-repeat: no-repeat;
        background-size: contain;
    }
</style>
```

It works OK when the image url is hard coded.

But when I want to change it dynamically in javascript, the image does not fit to the div container size and somehow it forget the "no-repeat"

jQuery:
```javascript
src = thumbnail.children('img').attr('src')
$('#detail-image-div').css("background", "url(" + src + ")  no-repeat 0 0");
```

So it needed an alternative way to make it work:

CSS:
```javascript
<style>
    :root {
        --background-image: "";
    }

    #detail-image-div{
        height: 100%;
        width: 50%;

        background: var(--background-image);
        background-position: right top;
        background-repeat: no-repeat;
        background-size: contain;
    }
</style>
```

jQuery:
```javascript
    var t = document.querySelector(':root');

    ...

    src = thumbnail.children('img').attr('src')
    t.style.setProperty('--background-image', "url(" + src + ")");
```

## 5. Ajax call uses cache
When I send the same ajax call, it well not connect and send request but it takes the result from the cache.
If you want to avoid this case, you have to tell explicitly this in the ajax request.

jQuery
```javascript
    let rawText = $.ajax({url: path, async: false, cache: false}).responseText;
```


## 6. Fade image to white

CSS:
```javascript
<style>

</style>
```
