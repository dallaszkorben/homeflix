/*
Collects data for Container Boxes and when it is done, it shows them in the Container

Parameters
sectionMap : A map where the thumbnail hierarchy is stored
sectionIndex : The index of the HTML's thumbnail-section <div> (inside the thumbnal-sections <div>) where the new Container should go
*/
class ObjThumbnailSection{
    /**
     * Delete the existing Containers and create a given number of Containers
     * 
     * <div id="thumbnail-section">
     *   <div id="thumbnail-section-history"> > </div>
     *
     *   <div class="thumbnail-container-block" id="container-block-1">
     *       <div class="thumbnail-container-title">Comedy</div>
     *       <div class="thumbnail-container" id="container-1">
     *       </div>
     *       <div class="thumbnail-container-space" id="container-space-1"></div>
     *   </div>
     *   <div class="thumbnail-container-block" id="container-block-2">
     *       <div class="thumbnail-container-title">Comedy</div>
     *       <div class="thumbnail-container" id="container-1">
     *       </div>
     *       <div class="thumbnail-container-space" id="container-space-1"></div>
     *   </div>   
     * </div>
     * 
     * @param {number} numberOfContainers 
     */
    constructor(defaultContainerIndex=0){
        this.oDescriptionContainer;
        this.numberOfContainers = 0;
        this.defaultContainerIndex = defaultContainerIndex;
        this.currentContainerIndex = -1;
        this.thumbnailContainerList = [];
        this.thumbnailIndexList = [];

        // Remove all elements from the <div id=thumbnail-sections> and <div id=detail-text-title> and <div id=detail-image-div>
        this.domThumbnailSection = $("#thumbnail-section");
        this.domThumbnailSection.empty();
        
        let domThumbnailSectionHistory = $("<div>",{
            id: "thumbnail-section-history",
            text: "> "
        });

        this.domThumbnailSection.append(domThumbnailSectionHistory);
     
        this.oDescriptionContainer = new ObjDescriptionContainer();
    }

    getDescriptionContainer(){
        return this.oDescriptionContainer;
    }

    addThumbnailContainerObject(title, thumbnailContainer){
        let containerIndex = this.thumbnailIndexList.length;

        let domThumbnailContainerBlock = $('<div>', {
            class: "thumbnail-container-block",
            id: "container-block-" + containerIndex
        });

        // Creates the Title JQuery element of the Thumbnail Container
        let domThumbnailContainerTitle = $("<div>",{
            class: "thumbnail-container-title",
            text: title
        });

        // Gets the Thumbnail Container JQuery Element
        let domThumbnailContainer = thumbnailContainer.getDom();

        // The ids must be changed as the ObjThumbnailContainer class has no idea about the id here (in the ObjThumbnailSection)
        let currentThumbnailIndex = thumbnailContainer.getDefaultThumbnailIndex();
        this.thumbnailIndexList.push(currentThumbnailIndex);
        this.thumbnailContainerList.push(thumbnailContainer);
        this.numberOfContainers++;

        let id = domThumbnailContainer.attr("id");
        domThumbnailContainer.attr("id", id.format("???", containerIndex));
        domThumbnailContainer.children('.thumbnail').each(function(){
            let element = $(this);
            let id=element.attr("id");
            element.attr("id",id.format("???", containerIndex));
        });

        // Creates the Space JQuery element after the Thumbnail Container
        let domThumbnailContainerSpace = $("<div>",{
            class: "thumbnail-container-space",
            id: "container-space-" + containerIndex
        });

        domThumbnailContainerBlock.append(domThumbnailContainerTitle);
        domThumbnailContainerBlock.append(domThumbnailContainer);
        domThumbnailContainerBlock.append(domThumbnailContainerSpace);
        this.domThumbnailSection.append(domThumbnailContainerBlock);

        // this variable should be refreshed every time when a new thumbnail is added
        this.domThumbnailContainerBlocks = $('#thumbnail-section .thumbnail-container-block');
    }

    selectDefault(){
        this.currentContainerIndex = 0;
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');

        this.showDetails();
    }

    // TODO: the currentThumbnailIndex should be fetched from ThumbnailContainer !!!
    showDetails(){
        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];
        let thumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex]
        let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex)

        let image = thumbnail.getDescriptionImageSource();
        let title = thumbnail.getTitle();
        let storyline = thumbnail.getStoryline();
        let credentials = thumbnail.getCredentials();
        let extra = thumbnail.getExtras();

        // Shows the actual Description
        this.oDescriptionContainer.refreshDescription(image, title, storyline, credentials, extra);
    }
    
    arrowRight(){
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        currentThumbnailIndex = (currentThumbnailIndex + 1) % domThumbnails.length;
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this.scrollThumbnails();
        this.thumbnailIndexList[this.currentContainerIndex] = currentThumbnailIndex;

        this.showDetails();
    }

    arrowLeft() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        currentThumbnailIndex = (currentThumbnailIndex - 1 + domThumbnails.length) % domThumbnails.length;
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this.scrollThumbnails();
        this.thumbnailIndexList[this.currentContainerIndex] = currentThumbnailIndex;
        this.showDetails();
    }

    arrowDown() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];
        
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        this.currentContainerIndex = (this.currentContainerIndex + 1) % this.numberOfContainers;
        domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this.scrollThumbnails();
        this.showDetails();
    };

    arrowUp() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');

        this.currentContainerIndex = (this.currentContainerIndex - 1 + this.numberOfContainers) % this.numberOfContainers;
        domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        // currentThumbnailIndex = 0;
        currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this. scrollThumbnails();
        this.showDetails();
    };

    clickOnThumbnail() {
    }

    scrollThumbnails() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail'); 
        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];

        // Vertical scroll 
        let sectionHeight = this.domThumbnailSection.height();
        let thumbnailContainerBlockHeight = this.domThumbnailContainerBlocks.eq(0).outerHeight(true);

        let sectionScrollTop = this.domThumbnailSection.scrollTop();
        let visibleContainers = Math.floor(sectionHeight / thumbnailContainerBlockHeight);

        //console.log(sectionHeight +"/" +thumbnailContainerBlockHeight + "=" + visibleContainers)

        if (this.currentContainerIndex >= visibleContainers + sectionScrollTop / thumbnailContainerBlockHeight) {
            this.domThumbnailSection.animate({ scrollTop: thumbnailContainerBlockHeight * (this.currentContainerIndex - visibleContainers + 1) }, 200);
        } else if (this.currentContainerIndex < sectionScrollTop / thumbnailContainerBlockHeight) {
            this.domThumbnailSection.animate({ scrollTop: thumbnailContainerBlockHeight * this.currentContainerIndex }, 200);
        }                    

        // Horizontal scroll
        let domContainer = $('#container-' + this.currentContainerIndex);
        let containerWidth = domContainer.width();
        let thumbnailWidth = domThumbnails.eq(0).outerWidth(true);

        let containerScrollLeft = domContainer.scrollLeft();
        let visibleThumbnails = Math.floor(containerWidth / thumbnailWidth);

        if (currentThumbnailIndex >= visibleThumbnails + containerScrollLeft / thumbnailWidth) {
            domContainer.animate({ scrollLeft: thumbnailWidth * (currentThumbnailIndex - visibleThumbnails + 1) }, 200);
        } else if (currentThumbnailIndex < containerScrollLeft / thumbnailWidth) {
            domContainer.animate({ scrollLeft: thumbnailWidth * currentThumbnailIndex }, 200);
        }
    }
}
   

class ObjThumbnailContainer{
    /**
     * <div class="thumbnail-container-block" id="container-block-1">
     *   <div class="thumbnail-container-title">Comedy</div>
     *   <div class="thumbnail-container" id="container-1">
     *   </div>
     *   <div class="thumbnail-container-space" id="container-space-1"></div>
     * </div>
     */
    constructor(defaultThumbnailIndex=0){            
        this.numberOfThumbnails = undefined;
        this.defaultThumbnailIndex = defaultThumbnailIndex;
        this.currentThumbnailIndex = undefined;
        this.thumbnailList = [];
        
        this.domThumbnailContainer = $("<div>",{
            class: "thumbnail-container",
            id: "container-{???}"
        });
    }

    getDom(){
        return this.domThumbnailContainer;
    }        

    getDefaultThumbnailIndex(){
        return this.defaultThumbnailIndex;
    }

    getThumbnail(thumbnailIndex){
        return this.thumbnailList[thumbnailIndex];
    }

    /**
     * 
     * @param {Number} recordId 
     * @param {Dict} thumbnail 
     * 
     * thumbnailDict = {
     *    "record_id": 123,
     *    "thumbnail_src": "images/categories/movie1.jpg",
     *    "description_src": "images/categories/movie.jpg",
     *    "title_thumb": "short title",
     *    "title": "translated title",
     *    "title_orig": "original title",
     *    "lang_orig": "hu",
     *    "storyline": "This is the story",
     *    "credentials": {
     *       "directors": ["David Linch"],
     *       "writers": ["Rhett Reese", "Paul Wernick"],
     *       "stars": ["Woody Harrelson", "Jesse Eisenberg", "Emma Stone"],
     *       "actors": ["Woody Harrelson", "Jesse Eisenberg", "Emma Stone"],
     *    }
     *    "extras": {
     *       "length": "01:47:57", 
     *       "year": 1989, 
     *       "origin": ["Hungary", "Germany", "Australia"], 
     *       "genre": ["Action", "Sci-fi"], 
     *       "theme": ["War", "AI", "Life"]
     *    }
     * };
     *
     * ====================================================
     *  
     * <div class="thumbnail" id="container-1_thumbnail-0">
     *   <div class="thumbnail-text-wrapper">
     *     <div class="thumbnail-text">1. box</div>
     *   </div>
     *   <img src="images/categories/movie.jpg" alt="Image">
     * </div>
     */
    addThumbnail(recordId, thumbnail){
        let title_thumb = thumbnail.getThumbnailTitle(); 
        let thumbnail_src = thumbnail.getThumbnailImageSource();

        let thumbnailIndex = this.thumbnailList.length;
        this.thumbnailList.push(thumbnail);
        let domThumbnail = $("<div>",{
            class: "thumbnail",
            id: "container-{???}-thumbnail-" + thumbnailIndex
        });
        let domThumbnailTextWrapper = $("<div>",{
            class: "thumbnail-text-wrapper",
        });
        let domThumbnailText = $("<div>",{
            class: "thumbnail-text",
            text: title_thumb
        });
        let domImg = $("<img>",{
            src: thumbnail_src,
            alt: "Image"
        });
        domThumbnailTextWrapper.append(domThumbnailText);
        domThumbnail.append(domThumbnailTextWrapper);
        domThumbnail.append(domImg);
        this.domThumbnailContainer.append(domThumbnail);
    }
}

class Thumbnail{

    /**
    * this.thumbnailDict = {
    *    "record_id": 123,
    *    "thumbnail_src": "images/categories/movie1.jpg",
    *    "description_src": "images/categories/movie.jpg",
    *    "title_thumb": "short title",
    *    "title": "translated title",
    *    "title_orig": "original title",
    *    "lang_orig": "hu",
    *    "storyline": "This is the story",
    *    "credentials": {
    *       "directors": ["David Linch"],
    *       "writers": ["Rhett Reese", "Paul Wernick"],
    *       "stars": ["Woody Harrelson", "Jesse Eisenberg", "Emma Stone"],
    *       "actors": ["Woody Harrelson", "Jesse Eisenberg", "Emma Stone"],
    *    }
    *    "extras": {
    *       "length": "01:47:57", 
    *       "year": 1989, 
    *       "origin": ["Hungary", "Germany", "Australia"], 
    *       "genre": ["Action", "Sci-fi"], 
    *       "theme": ["War", "AI", "Life"]
    *    }
    * };
    */
    
    constructor(){            
        this.thumbnailDict = {
        };    
    }

    setImageSources(thumbnail_src=undefined, descriptionSrc=undefined){
        if(thumbnail_src != undefined){
            this.thumbnailDict["thumbnail_src"] = thumbnail_src;
        }
        if(description_src != undefined){
            this.thumbnailDict["description_src"] = description_src;
        }
    }

    setTitles(lang_orig, original=undefined, translated=undefined, thumb=undefined){
        this.thumbnailDict["lang_orig"] = lang_orig;

        if(translated != undefined){
            this.thumbnailDict["title"] = translated;
        }else if(original != undefined){
            this.thumbnailDict["title"] = original;
        }

        if(thumb != undefined){
            this.thumbnailDict["title_thumb"] = thumb;
        }
    }
    
    setStoryline(storyline){
        if(storyline != undefined){
            this.thumbnailDict["storyline"] = storyline;
        }
    }

    setCredentials(directors=undefined, writers=undefined, stars=undefined, actors=undefined){
        this.thumbnailDict["credentials"] = {}
        if(directors != undefined && Array.isArray(directors)){
            this.thumbnailDict["credentials"]["directors"] = directors;
        }
        if(writers != undefined && Array.isArray(writers)){
            this.thumbnailDict["credentials"]["writers"] = writers;
        }
        if(stars != undefined && Array.isArray(stars)){
            this.thumbnailDict["credentials"]["stars"] = stars;
        }
        if(actors != undefined && Array.isArray(actors)){
            this.thumbnailDict["credentials"]["actors"] = actors;
        }
    }

    setExtras(length=undefined, year=undefined, origin=undefined, genre=undefined, theme=undefined){
        this.thumbnailDict["extras"] = {}
        if(length != undefined){
            this.thumbnailDict["extras"]["length"] = length;            
        }
        if(year != undefined){
            this.thumbnailDict["extras"]["year"] = year;
        }
        if(origin != undefined && Array.isArray(origin)){
            this.thumbnailDict["extras"]["origin"] = origin;            
        }
        if(genre != undefined && Array.isArray(genre)){
            this.thumbnailDict["extras"]["genre"] = genre;            
        }
        if(theme != undefined && Array.isArray(theme)){
            this.thumbnailDict["extras"]["theme"] = theme;            
        }
    }

    getThumbnailDict(){
        return this.thumbnailDict;
    }

    getThumbnailImageSource(){
        if("thumbnail_src" in this.thumbnailDict)
            return this.thumbnailDict["thumbnail_src"];
        return "";
    }

    getDescriptionImageSource(){
        if("description_src" in this.thumbnailDict)
            return this.thumbnailDict["description_src"];
        return "";
    }

    getTitle(){
            return this.thumbnailDict["title"];
        return "";
    }

    getThumbnailTitle(){
        if("title_thumb" in this.thumbnailDict)
            return this.thumbnailDict["title_thumb"];
        return "";
    }

    getStoryline(){
        if("storyline" in this.thumbnailDict)
            return this.thumbnailDict["storyline"];
        return ""
    }

    getCredentials(){
        if("credentials" in this.thumbnailDict)
            return this.thumbnailDict["credentials"];
        return {};
    }

    getExtras(){
        if("extras" in this.thumbnailDict)
            return this.thumbnailDict["extras"];
        return {};
    }
}


class ObjDescriptionContainer{
    constructor(){
        this.description_img={
            width: 0,
            height: 0
        }
    }

    /**
    * Refreshes the Description
    * It configures an onload listener on the new image.
    * When the image loaded, this function will calculate the size of the elements in the description and
    * it will show the details
    * 
    * @param {*} fileName 
    * @param {*} storyline 
    * @param {*} credential 
    */
    refreshDescription(fileName, title, storyline, credentials, extra){
        let mainObject = this;
        let descImg = new Image();
        descImg.src = fileName;

        // when the image loaded, the onload event will be fired
        descImg.onload = function(){
        
            // calculates the new size of the description image
            mainObject.description_img.height = descImg.height;
            mainObject.description_img.width = descImg.width;
        
            // Resizes the description section according to the size of the description image
            mainObject.resizeDescriptionSection();

            // -------------
            // --- title ---        
            // -------------
            let descTextTitle = $("#description-text-title");
            descTextTitle.empty();                
            descTextTitle.html(title);

            // -----------------
            // --- storyline ---        
            // -----------------
            let descTextStoryline = $("#description-text-storyline");
            descTextStoryline.empty();                
            descTextStoryline.html(storyline);
            // -----------------

            // -------------
            // --- extra ---
            // -------------

            // --- extra - year ---
            let descTextExtraYear = $("#description-text-extra-table-year");
            descTextExtraYear.empty();
            let textExtraYear = "";
            if ("year" in extra){
                textExtraYear += "•" + extra["year"] + "•";
            }
            descTextExtraYear.html(textExtraYear);

            // --- extra - length ---
            let descTextExtraLength = $("#description-text-extra-table-length");
            descTextExtraLength.empty();
            let textExtraLength = "";
            if ("length" in extra){
                textExtraLength += "   ";
                textExtraLength += extra["length"];
            }
            descTextExtraLength.html(textExtraLength);

            // --- extra - origin ---
            let descTextExtraOrigin = $("#description-text-extra-table-origin");
            descTextExtraOrigin.empty();
            let textExtraOrigin = "";
            if ("origin" in extra){
                let originList = extra["origin"];
                let first = true;
                for (let item of originList) {
                    if(first){
                        first = false;
                    }else{
                        textExtraOrigin += "•";
                    }
                    textExtraOrigin += item;
                }
            }
            descTextExtraOrigin.html(textExtraOrigin);

            // --- extra - genre ---
            let descTextExtraGenre = $("#description-text-extra-table-genre");
            descTextExtraGenre.empty();
            let textExtraGenre = "";
            if ("genre" in extra){
                let genreList = extra["genre"];
                let first = true;
                for (let item of genreList) {
                    if(first){
                        first = false;
                    }else{
                        textExtraGenre += "•";
                    }
                    textExtraGenre += item;
                }
            }
            descTextExtraGenre.html(textExtraGenre);

            // let extraTable = $("<table>",{
            //     border: 1,
            //     id: "description-text-extra-table"
            // });
            // descTextExtra.append(extraTable);
            // printExtra(extraTable, extra)

            // -------------------
            // --- credentials ---
            // -------------------

            let descTextCredentials = $("#description-text-credentials");                
            descTextCredentials.empty();

            let credTable = $("<table>",{
                border: 0,
                id: "description-text-credentials-table"
            });
            descTextCredentials.append(credTable);

            mainObject.printCredentals(credTable, credentials, "directors", "Directors:");
            mainObject.printCredentals(credTable, credentials, "writers", "Writers:");
            mainObject.printCredentals(credTable, credentials, "stars", "Stars:");
            // -------------------
    
        }

        // Loads the new image, which will trigger the onload event
        let description_image = "url(" + descImg.src + ")";
        t.style.setProperty('--description-image', description_image);
    }


    /**
    * It resizes the description image and the description text wrapper (in the CSS) according to the available place
    * It is called when the size of the description section changed
    * Typically used by the ResizeObserver
    * 
    */
    resizeDescriptionSection(){
        let domDescriptionSectionDiv = $("#description-section");
        let sectionHeight = domDescriptionSectionDiv.height();

        let wrapperHeight = domDescriptionSectionDiv.innerHeight();
        let wrapperWidth = domDescriptionSectionDiv.innerWidth();

        let newDescImgWidth = sectionHeight * this.description_img.width / this.description_img.height;

        // Set the width of the image accordingto its aspect ration and the available height
        t.style.setProperty('--description-image-width', newDescImgWidth + 'px');

        // Set the size of the text-wrapper div to cover the whole available space
        t.style.setProperty('--description-text-wrapper-height', wrapperHeight + 'px');
        t.style.setProperty('--description-text-wrapper-width', wrapperWidth + 'px');

        let domDescTextStoryline = $("#description-text-storyline");
    
        let posStoryline = domDescTextStoryline.position().top;
        let storylineWidth = wrapperHeight - posStoryline - 2;
        t.style.setProperty('--description-text-storyline-height', storylineWidth + 'px');
        t.style.setProperty('--description-text-credentials-height', storylineWidth + 'px');  
    }

    printCredentals(table, dict, id, title){
        if (id in dict){
            let first = true;
            let listItems = dict[id];
            for (let item of listItems) {
                let line = $("<tr>");
                let column = $("<td>");
                if (first){
                    column.text(title);
                }
                first = false;
                line.append(column);
    
                column = $("<td>");
                column.text(item);
                line.append(column);
    
                table.append(line);
            }
        }
    }
    
}
