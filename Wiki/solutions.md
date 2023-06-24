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
```python
self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
```



###2. Media selector:
HTML
```javascript
<div id="thumbnail-container">
  <div class="thumbnail">
    <img src="images/image1.jpg" alt="Thumbnail 1" />
  </div>
  <div class="thumbnail">
    <img src="images/image2.jpg" alt="Thumbnail 2" />
  </div>
  <div class="thumbnail">
    <img src="images/image3.jpg" alt="Thumbnail 3" />
  </div>
  <!-- További thumbnail-ök hozzáadása itt -->
</div>
<div id="arrow-container">
  <span id="left-arrow">&lt;</span>
  <span id="right-arrow">&gt;</span>
</div>
```

CSS
```javascript
    .thumbnail-container {
        width: 100%;
        overflow: hidden; 
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        justify-content: flex-start;
        align-items: flex-start;
        border:3px blue solid;
    }

    .thumbnail {
        width: 200px;
        height: 150;
        margin: 0px;
        border: 3px solid transparent;
        background-color: black;
  
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .thumbnail img {
        width: 200px;
        height: auto;
        max-height: 150px;
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

  // Kezdetben a legelső thumbnail legyen kiválasztva
  thumbnails.eq(currentIndex).css('border-color', 'white');

  $('#right-arrow').click(function() {
    thumbnails.eq(currentIndex).css('border-color', 'transparent');
    currentIndex = (currentIndex + 1) % thumbnails.length;
    thumbnails.eq(currentIndex).css('border-color', 'white');
    scrollThumbnails();
  });

  $('#left-arrow').click(function() {
    thumbnails.eq(currentIndex).css('border-color', 'transparent');
    currentIndex = (currentIndex - 1 + thumbnails.length) % thumbnails.length;
    thumbnails.eq(currentIndex).css('border-color', 'white');
    scrollThumbnails();
  });

  function scrollThumbnails() {
    var container = $('#thumbnail-container');
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
