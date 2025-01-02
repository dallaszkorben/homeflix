/*
Collects data for Container Boxes and when it is done, it shows them in the Container

Parameters
sectionMap : A map where the thumbnail hierarchy is stored
sectionIndex : The index of the HTML's scroll-section <div> (inside the thumbnal-sections <div>) where the new Container should go
*/
class ObjScrollSection{
    /**
     * Delete the existing Containers and create a given number of Containers
     * 
     * <div id="scroll-section">
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
    // TODO: change current to focused
    constructor(oContainerGenerator, history={text:"", link:""}){
        this.oContainerGenerator = oContainerGenerator;
        this.historyDict = history;

        this.defaultContainerIndex = 0
        this.oDescriptionContainer;
        this.numberOfContainers = 0;
        this.currentContainerIndex = -1;
        this.thumbnailContainerList = [];
        this.focusedThumbnailList = [];  

        this.oDescriptionContainer = new ObjDescriptionContainer();        

        this.resetDom();

        this.oContainerGenerator.showContainers(this);
    }

    resetDom(){
        // Remove all elements from the <div id=scroll-section> and <div id=detail-text-title> and <div id=detail-image-div>
        this.domScrollSection = $("#scroll-section");
        this.domScrollSection.empty();

        let tsht = $("#history-section-text");
        tsht.html(this.historyDict["text"]);

        let tshl = $("#history-section-link");
        tshl.html(this.historyDict["link"]);
    }

    /**
     * Builds up new DOM for ControllerSection after it was taken out from the history
     */
    buildUpDom(){
        this.resetDom();

        for(let containerIndex=0; containerIndex<this.thumbnailContainerList.length; containerIndex++){
            let objThumbnailContainer = this.thumbnailContainerList[containerIndex];

            objThumbnailContainer.buildUpDom();
            let domThumbnailContainer = objThumbnailContainer.getDom();
            
            let id = domThumbnailContainer.attr("id");
            domThumbnailContainer.attr("id", id.format("???", containerIndex));
            domThumbnailContainer.children('.thumbnail').each(function(){
                let element = $(this);
                let id=element.attr("id");
                element.attr("id",id.format("???", containerIndex));
            });

            let domThumbnailContainerBlock = $('<div>', {
                class: "thumbnail-container-block",
                id: "container-block-" + containerIndex
            });
    
            // Creates the Title JQuery element of the Thumbnail Container
            let domThumbnailContainerTitle = $("<div>",{
                class: "thumbnail-container-title",
                text: objThumbnailContainer.getTitle()
            });

            let domThumbnailContainerSpace = $("<div>",{
                class: "thumbnail-container-space",
                id: "container-space-" + containerIndex
            });
    
            domThumbnailContainerBlock.append(domThumbnailContainerTitle);
            domThumbnailContainerBlock.append(domThumbnailContainer);
            domThumbnailContainerBlock.append(domThumbnailContainerSpace);
            this.domScrollSection.append(domThumbnailContainerBlock);
        }
        
        this.domThumbnailContainerBlocks = $('#scroll-section .thumbnail-container-block');

        this.focus();
    }

    getDescriptionContainer(){
        return this.oDescriptionContainer;
    }

    addThumbnailContainerObject(thumbnailContainer){
        let refToThis = this;
        let containerIndex = this.focusedThumbnailList.length;

        let domThumbnailContainerBlock = $('<div>', {
            class: "thumbnail-container-block",
            id: "container-block-" + containerIndex
        });

        // Creates the Title JQuery element of the Thumbnail Container
        let domThumbnailContainerTitle = $("<div>",{
            class: "thumbnail-container-title",
            text: thumbnailContainer.getTitle()
        });

        // Gets the Thumbnail Container JQuery Element
        let domThumbnailContainer = thumbnailContainer.getDom();

        // The ids must be changed as the ObjThumbnailContainer class has no idea about the id here (in the ObjScrollSection)
        let currentThumbnailIndex = thumbnailContainer.getDefaultThumbnailIndex();
        this.focusedThumbnailList.push(currentThumbnailIndex);
        this.thumbnailContainerList.push(thumbnailContainer);
        this.numberOfContainers++;

        let id = domThumbnailContainer.attr("id");
        domThumbnailContainer.attr("id", id.format("???", containerIndex));
        domThumbnailContainer.children('.thumbnail').each(function(){
            let thumbnailElement = $(this);
            let id=thumbnailElement.attr("id");
            thumbnailElement.attr("id",id.format("???", containerIndex));
            thumbnailElement.click(function(){
                refToThis.clickedOnThumbnail($(this).attr('id'));
            });
        });

        // Creates the Space JQuery element after the Thumbnail Container
        let domThumbnailContainerSpace = $("<div>",{
            class: "thumbnail-container-space",
            id: "container-space-" + containerIndex
        });

        domThumbnailContainerBlock.append(domThumbnailContainerTitle);
        domThumbnailContainerBlock.append(domThumbnailContainer);
        domThumbnailContainerBlock.append(domThumbnailContainerSpace);
        this.domScrollSection.append(domThumbnailContainerBlock);

        // this variable should be refreshed every time when a new thumbnail is added
        this.domThumbnailContainerBlocks = $('#scroll-section .thumbnail-container-block');
    }

    focusDefault(){
        this.currentContainerIndex = 0;
        this.focus();
    }

    focus(){
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');

        this.scrollThumbnails();
        this.showDetails();
    }

    // getFocusedHistoryTitle(){
    //     let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
    //     let thumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex];
    //     let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex);
    //     return thumbnail.getHistoryTitle();
    // } 

    getFocusedThubnailContainerTitle(){
        let oThumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex];
        return oThumbnailContainer.title;
    }

    getSelectedThumbnalFunctionForSelection(){
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        let thumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex];
        let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex);
        let function_for_selection = thumbnail.getFunctionForSelection();
        return function_for_selection;
    }

    // TODO: the currentThumbnailIndex should be fetched from ThumbnailContainer !!!
    showDetails(){
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
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
    
    clickedOnThumbnail(id){
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        const re = /\d+/g
        let match = id.match(re);
        let clickedContainerIndex = parseInt(match[0]);
        let clickedThumbnailIndex = parseInt(match[1]);

        // Enter needed
        if(this.currentContainerIndex==clickedContainerIndex && currentThumbnailIndex==clickedThumbnailIndex){

            // Simulate an Enter press on the "document"
            let e = jQuery.Event("keydown");
            e.which = 13;  //Enter
            e.keyCode = 13;
            $(document).trigger(e);

        // Focus needed
        }else{

            // Hide the current focus
            let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
            domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
            this.currentContainerIndex = clickedContainerIndex;
            domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
            currentThumbnailIndex = clickedThumbnailIndex;

            // Show the current focus
            domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
            this.focusedThumbnailList[this.currentContainerIndex] = currentThumbnailIndex;
            this.scrollThumbnails();
            this.showDetails();
        }
    }

    arrowRight(){
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        currentThumbnailIndex = (currentThumbnailIndex + 1) % domThumbnails.length;
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this.focusedThumbnailList[this.currentContainerIndex] = currentThumbnailIndex;
        this.scrollThumbnails();
        this.showDetails();
    }

    arrowLeft() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        currentThumbnailIndex = (currentThumbnailIndex - 1 + domThumbnails.length) % domThumbnails.length;
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this.focusedThumbnailList[this.currentContainerIndex] = currentThumbnailIndex;
        this.scrollThumbnails();
        this.showDetails();
    }

    arrowDown() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        this.currentContainerIndex = (this.currentContainerIndex + 1) % this.numberOfContainers;
        domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this.scrollThumbnails();
        this.showDetails();
    };

    arrowUp() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');        
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');

        this.currentContainerIndex = (this.currentContainerIndex - 1 + this.numberOfContainers) % this.numberOfContainers;
        domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
        this. scrollThumbnails();
        this.showDetails();
    };

    scrollThumbnails() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail'); 
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        // Vertical scroll 
        let sectionHeight = this.domScrollSection.height();
        let thumbnailContainerBlockHeight = this.domThumbnailContainerBlocks.eq(0).outerHeight(true);

        let sectionScrollTop = this.domScrollSection.scrollTop();
        let visibleContainers = Math.floor(sectionHeight / thumbnailContainerBlockHeight);

        if (this.currentContainerIndex >= visibleContainers + sectionScrollTop / thumbnailContainerBlockHeight) {
            this.domScrollSection.animate({ scrollTop: thumbnailContainerBlockHeight * (this.currentContainerIndex - visibleContainers + 1) }, 200);
        } else if (this.currentContainerIndex < sectionScrollTop / thumbnailContainerBlockHeight) {
            this.domScrollSection.animate({ scrollTop: thumbnailContainerBlockHeight * this.currentContainerIndex }, 200);
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
    constructor(title, defaultThumbnailIndex=0){            
        this.title = title
        this.numberOfThumbnails = undefined;
        this.defaultThumbnailIndex = defaultThumbnailIndex;
        this.currentThumbnailIndex = undefined;
        this.thumbnailList = [];
        
        this.resetDom();
    }

    resetDom(){
        this.domThumbnailContainer = $("<div>",{
            class: "thumbnail-container",
            id: "container-{???}"
        });
        this.domThumbnailContainer.empty();
    }

    /**
     * Builds up new DOM for ThumbnailContainer
     * Called from the ScrollSection after it was taken out from the history
     */
    buildUpDom(){
        this.resetDom();

        for(let thumbnailIndex=0; thumbnailIndex<this.thumbnailList.length; thumbnailIndex++){
            let objThumbnail = this.thumbnailList[thumbnailIndex];

            let title_thumb = objThumbnail.getThumbnailTitle(); 
            let thumbnail_src = objThumbnail.getThumbnailImageSource();

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

    getDom(){
        return this.domThumbnailContainer;
    }        

    getTitle(){
        return this.title;
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

//        this.thumbnailDomList.push(domThumbnail);
    }
}

class Thumbnail{

    /**
    * this.thumbnailDict = {
    *    "record_id": 123,
    *    "thumbnail_src": "images/categories/movie1.jpg",
    *    "description_src": "images/categories/movie.jpg",
    *    "title_history": "history title",
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
        this.selection_fn = undefined;
        this.thumbnailDict = {
        };    
    }

    setFunctionForSelection(function_for_selection){
        this.function_for_selection = function_for_selection;
    }
    
    getFunctionForSelection(){
        if(this.function_for_selection){
            return this.function_for_selection;
        }else{
            return undefined;
        }
    }

    setImageSources(thumbnail_src=undefined, description_src=undefined){
        if(thumbnail_src != undefined){
            this.thumbnailDict["thumbnail_src"] = thumbnail_src;
        }
        if(description_src != undefined){
            this.thumbnailDict["description_src"] = description_src;
        }
    }

    setTitles(lang_orig, original=undefined, translated=undefined, thumb=undefined, history=undefined){
        this.thumbnailDict["lang_orig"] = lang_orig;

        //                                                               translated  original
        // requested ≠ original requested exist,          original exist         ✔        ✔
        // requested ≠ original requested does not exist, original exist         ❌        ✔
        // requested = original                                                  ✔        ❌        
        //

        if(translated == undefined){
            this.thumbnailDict["title"] = original + " (" + lang_orig + ")";
        }else if(translated != undefined){
            this.thumbnailDict["title"] = translated;
        }

        if(thumb != undefined){
            this.thumbnailDict["title_thumb"] = thumb;
        }

        if(history != undefined){
            this.thumbnailDict["title_history"] = history;
        }
    }
    
    setStoryline(storyline){
        if(storyline != undefined){
            this.thumbnailDict["storyline"] = storyline;
        }
    }

    setCredentials(directors=undefined, writers=undefined, stars=undefined, actors=undefined, voices=undefined){
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

    setExtras(length=undefined, date=undefined, origins=undefined, genres=undefined, themes=undefined){
        this.thumbnailDict["extras"] = {}
//        if(length != undefined){
            this.thumbnailDict["extras"]["length"] = length;            
//        }
//        if(year != undefined){
            this.thumbnailDict["extras"]["date"] = date;
//        }
//        if(origin != undefined && Array.isArray(origin)){
            this.thumbnailDict["extras"]["origins"] = origins;            
//        }
//        if(genre != undefined && Array.isArray(genre)){
            this.thumbnailDict["extras"]["genres"] = genres;            
//        }
//        if(theme != undefined && Array.isArray(theme)){
            this.thumbnailDict["extras"]["themes"] = themes;            
//        }
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

    getHistoryTitle(){
        if("title_history" in this.thumbnailDict)
            return this.thumbnailDict["title_history"];
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
    * <div id="description-section">
    *   <div id="description-text-div">
    *       <div id="description-text-wrapper">
    *           <div id="description-text-title"></div>
    *           <div id="description-text-extra">
    *               <table border="0" id="description-text-extra-table">
    *                   <tr>
    *                       <td id="description-text-extra-table-year"></td>
    *                       <td id="description-text-extra-table-length"></td>
    *                   </tr>
    *                   <tr>
    *                       <td></td>
    *                       <td id="description-text-extra-table-origin"></td>
    *                   </tr>
    *                   <tr>
    *                       <td></td>
    *                       <td id="description-text-extra-table-genre"></td>
    *                   </tr>
    *               </table>
    *           </div>
    *           <div id="description-text-storyline"></div>
    *           <div id="description-text-credentials"></div>
    *       </div>
    *   </div>
    *   <div id="description-image"></div>
    *<div>
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
            let descTextExtraDate = $("#description-text-extra-date");
            descTextExtraDate.empty();
            let textExtraDate = "";
            if ("date" in extra && extra["date"]){
                textExtraDate += "" + extra["date"] + "";
            }
            descTextExtraDate.html(textExtraDate);

            // --- extra - length ---
            let descTextExtraLength = $("#description-text-extra-length");
            descTextExtraLength.empty();
            let textExtraLength = "";
            if ("length" in extra && extra["length"]){
                textExtraLength += "   ";
                textExtraLength += extra["length"];
            }
            descTextExtraLength.html(textExtraLength);

            // --- extra - origin ---
            let descTextExtraOrigin = $("#description-text-extra-block-origin");
            descTextExtraOrigin.empty();
            let textExtraOrigin = "";
            if ("origins" in extra && extra["origins"]){
                let originList = extra["origins"];
                let first = true;
                for (let item of originList) {
                    if(first){
                        first = false;
                    }else{
                        textExtraOrigin += " • ";
                    }
                    textExtraOrigin += item;
                }
            }
            descTextExtraOrigin.html(textExtraOrigin);

            // --- extra - genre ---
            let descTextExtraGenre = $("#description-text-extra-block-genre");
            descTextExtraGenre.empty();
            let textExtraGenre = "";
            if ("genres" in extra && extra["genres"]){
                let genreList = extra["genres"];
                let first = true;
                for (let item of genreList) {
                    if(first){
                        first = false;
                    }else{
                        textExtraGenre += " • ";
                    }
                    textExtraGenre += item;
                }
            }
            descTextExtraGenre.html(textExtraGenre);

            // --- extra - theme ---
            let descTextExtraTheme = $("#description-text-extra-block-theme");
            descTextExtraTheme.empty();
            let textExtraTheme = "";
            if ("themes" in extra && extra["themes"]){
                let themeList = extra["themes"];
                let first = true;
                for (let item of themeList) {
                    if(first){
                        first = false;
                    }else{
                        textExtraTheme += " • ";
                    }
                    textExtraTheme += item;
                }
            }
            descTextExtraTheme.html(textExtraTheme);

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

            mainObject.printCredentals(credTable, credentials, "directors", translated_titles['director'] + ":");
            mainObject.printCredentals(credTable, credentials, "writers", translated_titles['writer'] + ":");
            mainObject.printCredentals(credTable, credentials, "stars", translated_titles['star'] + ":")
            mainObject.printCredentals(credTable, credentials, "actors", translated_titles['actor'] + ":")
            mainObject.printCredentals(credTable, credentials, "voices", translated_titles['voice'] + ":")
            // -------------------
    
            // Resizes the description section according to the size of the description image
            mainObject.resizeDescriptionSection();
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

        let domDescriptionImageDiv = $("#description-image");
        let description_image_border_sum_width = domDescriptionImageDiv.outerWidth()-domDescriptionImageDiv.innerWidth();
        let description_image_border_sum_height = domDescriptionImageDiv.outerHeight()-domDescriptionImageDiv.innerHeight();
        
        let description_image_outer_width = this.description_img.width + description_image_border_sum_width;
        let description_image_outer_height = this.description_img.height + description_image_border_sum_height;

        let wrapperHeight = domDescriptionSectionDiv.innerHeight();
        let wrapperWidth = domDescriptionSectionDiv.innerWidth();

        let imageInnerHeight = wrapperHeight - description_image_border_sum_height;
        let newDescImgWidth = imageInnerHeight * description_image_outer_width / description_image_outer_height;

        // Set the width of the image accordingto its aspect ration and the available height
        t.style.setProperty('--description-image-width', newDescImgWidth + 'px');

        // Set the size of the text-wrapper div to cover the whole available space
        t.style.setProperty('--description-text-wrapper-height', wrapperHeight + 'px');
        t.style.setProperty('--description-text-wrapper-width', wrapperWidth + 'px');

        // Set the description-text-area-div height => here are the storyline and credentials, next to each other
        let domDescriptionTextWrapper = $("#description-text-wrapper");
        let textWrapperHeight = domDescriptionTextWrapper.innerHeight();
        let domDescriptionTextTitle = $("#description-text-title");
        let titleHeight = domDescriptionTextTitle.outerHeight();
        let domDescriptionTextExtra = $("#description-text-extra");
        let extraHeight = domDescriptionTextExtra.outerHeight();
        let domDescriptionTextArea = $("#description-text-area-div");
        let areaOuterHeight = domDescriptionTextArea.outerHeight();
        let areaInnerHeight = domDescriptionTextArea.innerHeight()
        let areaHeightBorder = areaOuterHeight - areaInnerHeight;
        let storylineHeight = textWrapperHeight - titleHeight - extraHeight - areaHeightBorder;

        t.style.setProperty('--description-text-storyline-height', storylineHeight + 'px');
        t.style.setProperty('--description-text-credentials-height', storylineHeight + 'px');  
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


class History{
    constructor(){
        this.levelList = [];
    }

    addNewLevel(objScrollSection){
        let text = objScrollSection.getFocusedThubnailContainerTitle();
        this.levelList.push({"text": text, "obj": objScrollSection});
    }

    getLevels(){
        let text = "";
        let link = "";

        for(let i=0; i<this.levelList.length-1; i++){
            text += this.levelList[i]["text"] + " >&nbsp;";
        }
        
        link = this.levelList.length ? " " + this.levelList[this.levelList.length - 1]["text"] : "";
        return {"text": text, "link": link};

    }

    popLevel(){
        if(this.levelList.length){
            let level = this.levelList.pop();
            return level["obj"];
        }else{
            return undefined;
        }
    }
}

class FocusTask {
    static Menu = new FocusTask('menu');
    static Player = new FocusTask('player');  
    constructor(name) {
      this.name = name
    }
}


class ThumbnailController{
    constructor(objScrollSection){
        this.history = new History();
        this.objScrollSection = objScrollSection;
        this.focusTask = FocusTask.Menu;
        
        let tshl = $("#history-section-link");
        tshl.click(function() {
            let esc = $.Event("keydown", { keyCode: 27 });
            $(document).trigger(esc);
        });
    }

    /*
    After the size of the description-section changed, the description-image size recalculation is needed.

    */
    resizeDescriptionSection(){
        //this.objScrollSection.focus();
        this.objScrollSection.getDescriptionContainer().resizeDescriptionSection();

    }

    generateScrollSection(oContainerGenerator, history={text:"", link:""}){
        let oScrollSection = new ObjScrollSection(oContainerGenerator, history);
        oScrollSection.focusDefault();
        return oScrollSection;
    }

    enter(){
        let refToThis = this;
        if(this.focusTask === FocusTask.Menu){

            // fetch the generator function of the thumbnail in the focus
            let functionForSelection = this.objScrollSection.getSelectedThumbnalFunctionForSelection();       

            // If the selected thumbnail will produce a sub-menu
            if("menu" in functionForSelection){

                this.focusTask = FocusTask.Menu;

                // We get one level deeper in the history
                this.history.addNewLevel(this.objScrollSection);        

                // take the generator's function
                let getGeneratorFunction = functionForSelection["menu"];

                // and call the generator's function to produce a new Container Generator
                let oContainerGenerator = getGeneratorFunction();
            
                // Shows the new ScrollSection generated by the Container Generator
                this.objScrollSection = this.generateScrollSection(oContainerGenerator, this.history.getLevels());

            }else if("play" in functionForSelection){
                 
                this.focusTask = FocusTask.Player;

                // take the getCardId function
                let getCardIdFunction = functionForSelection["play"];
                let medium_path = getCardIdFunction();
        
                if (medium_path != null){
                    let player = $("#video_player")[0];
                    let domPlayer = $("#video_player");

                    var sourceElement = $('#video_player').find('source');
                    if (sourceElement.length > 0) {
                        sourceElement.remove();
                    }

                    var newSourceElement = $('<source>');
                    newSourceElement.attr('src', medium_path);
                    // newSourceElement.attr('type', 'video/mkv');
                    $('#video_player').append(newSourceElement);
                                
                    if (player.requestFullscreen) {
                        player.requestFullscreen();
                    } else if (elem.msRequestFullscreen) {
                        player.msRequestFullscreen();
                    } else if (elem.mozRequestFullScreen) {
                        player.mozRequestFullScreen();
                    } else if (elem.webkitRequestFullscreen) {
                        player.webkitRequestFullscreen();
                    }

                                // video.addEventListener('keydown', function(event) {
                                //     console.log(event);
                                //     if (event.key === 'ArrowLeft') {
                                //         console.log('Arrow Left key pressed');
                                //     } else if (event.key === 'ArrowRight') {
                                //         console.log('Arrow Right key pressed');
                                //     } else if (event.key === 'Tab') {
                                //         console.log('Tab key pressed');
                                //         $('#video_player').focus();
                                //     }
                                // });

                    player.load();
                    player.controls = true; 
                    player.autoplay = true;                               
                    player.play();

                    $('#video_player').bind('webkitfullscreenchange mozfullscreenchange fullscreenchange', function(e) {
                        var state = document.fullScreen || document.mozFullScreen || document.webkitIsFullScreen;

                        // If exited of full screen
                        if(!state){
                            //this.style.display = 'none';
                            //this.pause();
                            //var sourceElement = $('#video_player').find('source');
                            //if (sourceElement.length > 0) {
                            //    sourceElement.remove();
                            //}
                            //// Ez nem mukodik
                            //$("#section-0_container-0").focus();

                            //player.hidden=true;
                            domPlayer.hide();
                            player.pause();
                            player.height = 0;
                            newSourceElement.attr('src', "");
                            let sourceElement = domPlayer.find('source');
                            if (sourceElement.length > 0) {
                                sourceElement.remove();
                            }

                            refToThis.focusTask = FocusTask.Menu;

//                            $(document).trigger('focus');
//                            $(document).focus();
//                            refToThis.objScrollSection.focus();
                        }
                    });
                    player.style.display = 'block';
                
                    // It is important to have this line, otherwise you can not control the voice level
                    $('#video_player').focus();

                }
            }
        }
    }

    escape(){
        if(this.focusTask === FocusTask.Menu){

            let oT = this.history.popLevel();
            if (oT){
                this.objScrollSection = oT;
                this.objScrollSection.buildUpDom();
            }
        }else if(this.focusTask === FocusTask.Player){
            this.focusTask = FocusTask.Menu;
        }
    }

    arrowLeft(){
        if(this.focusTask === FocusTask.Menu){
            this.objScrollSection.arrowLeft();
        }
    }

    arrowUp(){
        if(this.focusTask === FocusTask.Menu){
            this.objScrollSection.arrowUp();
        }
    }

    arrowRight(){
        if(this.focusTask === FocusTask.Menu){
            this.objScrollSection.arrowRight();
        }
    }

    arrowDown(){
        if(this.focusTask === FocusTask.Menu){
            this.objScrollSection.arrowDown();
        }
    }
}