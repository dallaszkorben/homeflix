/*
Collects data for Container Boxes and when it is done, it shows them in the Container

Parameters
sectionMap : A map where the thumbnail hierarchy is stored
sectionIndex : The index of the HTML's scroll-section <div> (inside the thumbnal-sections <div>) where the new Container should go
*/
class ObjScrollSection {
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
    constructor({ oContainerGenerator, historyLevels = { text: "", link: "" }, objThumbnailController = null }) {
        this.oContainerGenerator = oContainerGenerator;
        this.historyLevels = historyLevels;

        this.defaultContainerIndex = 0
        this.oDescriptionContainer;
        this.numberOfContainers = 0;
        this.currentContainerIndex = -1;
        this.thumbnailContainerList = [];
        this.focusedThumbnailList = [];

        this.oDescriptionContainer = new ObjDescriptionContainer(this);
        this.oDescriptionContainer.setThumbnailController(objThumbnailController);

        this.resetDom();

        this.oContainerGenerator.showContainers(this)
    }

    resetDom() {
        // Remove all elements from the <div id=scroll-section> and <div id=detail-text-title> and <div id=detail-image-div>
        this.domScrollSection = $("#scroll-section");
        this.domScrollSection.empty();

        let tsht = $("#history-section-text");
        tsht.html(this.historyLevels["text"]);

        let tshl = $("#history-section-link");
        tshl.html(this.historyLevels["link"]);
    }

    /**
     * Builds up new DOM for ControllerSection after it was taken out from the history
     */
    buildUpDom() {
        this.resetDom();
        let refToThis = this;

        for (let containerIndex = 0; containerIndex < this.thumbnailContainerList.length; containerIndex++) {
            let objThumbnailContainer = this.thumbnailContainerList[containerIndex];

            objThumbnailContainer.buildUpDom();
            let domThumbnailContainer = objThumbnailContainer.getDom();

            let id = domThumbnailContainer.attr("id");
            domThumbnailContainer.attr("id", id.format("???", containerIndex));
            domThumbnailContainer.children('.thumbnail').each(function () {
                let element = $(this);
                let id = element.attr("id");
                element.attr("id", id.format("???", containerIndex));

                // Add click listener on thumbnail. It must be set on the buildUpDome again
                element.click(function () {
                    refToThis.clickedOnThumbnail($(this).attr('id'));
                });
            });

            let domThumbnailContainerBlock = $('<div>', {
                class: "thumbnail-container-block",
                id: "container-block-" + containerIndex
            });

            // Creates the Title JQuery element of the Thumbnail Container
            let domThumbnailContainerTitle = $("<div>", {
                class: "thumbnail-container-title",
                text: objThumbnailContainer.getTitle()
            });

            let domThumbnailContainerSpace = $("<div>", {
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

    getDescriptionContainer() {
        return this.oDescriptionContainer;
    }

    addThumbnailContainerObject(thumbnailContainer) {
        let refToThis = this;
        let containerIndex = this.focusedThumbnailList.length;

        let domThumbnailContainerBlock = $('<div>', {
            class: "thumbnail-container-block",
            id: "container-block-" + containerIndex
        });

        // Creates the Title JQuery element of the Thumbnail Container
        let domThumbnailContainerTitle = $("<div>", {
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
        domThumbnailContainer.children('.thumbnail').each(function () {
            let thumbnailElement = $(this);
            let id = thumbnailElement.attr("id");
            thumbnailElement.attr("id", id.format("???", containerIndex));

            // Add click listener on thumbnail
            thumbnailElement.click(function () {
                refToThis.clickedOnThumbnail($(this).attr('id'));
            });
        });

        // Creates the Space JQuery element after the Thumbnail Container
        let domThumbnailContainerSpace = $("<div>", {
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

    focusDefault() {
        this.currentContainerIndex = 0;
        this.focus();
    }

    focus() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');

        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        domThumbnails.eq(currentThumbnailIndex).css('border-color', thumbnail_border_color);

        this.scrollThumbnails();
        this.showDetails();
    }

    getFocusedThubnailContainerTitle() {
        let oThumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex];
        return oThumbnailContainer.title;
    }

    getSelectedThumbnalFunctionForSelection() {
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        let thumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex];
        let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex);
        let function_for_selection = thumbnail.getFunctionForSelection();
        return function_for_selection;
    }

    refreshFocusedThumbnailProgresBar(recent_position){

        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        let thumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex];
        let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex);
        let extras = thumbnail.getExtras();
        let recent_state = extras["recent_state"];
        let full_time = extras["full_time"]; 
        let net_start_time = extras["net_start_time"];
        let net_stop_time = extras["net_stop_time"];
      
        recent_state["recent_position"] = recent_position;
        extras["recent_state"] = recent_state;
        thumbnail.setExtras(extras);

        let progress_percentage;
        // full_time != null && full_time > 600 && 
        if(recent_position != 0 && recent_position >= net_start_time && recent_position < net_stop_time){
            progress_percentage = 100 * recent_position / full_time;
        }else{
            progress_percentage = 0;
        }

        let bar_wrapper = domThumbnails.eq(currentThumbnailIndex).find(".thumbnail-play-progress-bar-wrapper");
        let bar = domThumbnails.eq(currentThumbnailIndex).find(".thumbnail-play-progress-bar")

        bar.css('width', progress_percentage + '%');

        if(progress_percentage == 0){
            bar_wrapper.hide()
        }else{
            bar_wrapper.show()
        }
    }

    // TODO: the currentThumbnailIndex should be fetched from ThumbnailContainer !!!
    showDetails() {
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];
        let thumbnailContainer = this.thumbnailContainerList[this.currentContainerIndex]
        let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex)
        let card_id = null;

        if (thumbnail != undefined) {
            let single = thumbnail.function_for_selection.single;
            if("medium_dict" in single){
                card_id = single.medium_dict["card_id"];
            }

            let image = thumbnail.getDescriptionImageSource();
            let title = thumbnail.getTitle();
            let storyline = thumbnail.getStoryline();
            let lyrics = thumbnail.getLyrics();
            let credentials = thumbnail.getCredentials();
            let extra = thumbnail.getExtras();
            let appendix = thumbnail.getAppendix();

            // Shows the actual Description
            this.oDescriptionContainer.refreshDescription(thumbnail, card_id, image, title, storyline, lyrics, credentials, extra, appendix);
        }
    }

    clickedOnThumbnail(id) {
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        const re = /\d+/g
        let match = id.match(re);
        let clickedContainerIndex = parseInt(match[0]);
        let clickedThumbnailIndex = parseInt(match[1]);

        // Enter needed
        if (this.currentContainerIndex == clickedContainerIndex && currentThumbnailIndex == clickedThumbnailIndex) {

            // Simulate an Enter press on the "document"
            let e = jQuery.Event("keydown");
            e.which = 13;  //Enter
            e.keyCode = 13;
            $(document).trigger(e);

        // Focus needed
        } else {

            // Hide the current focus
            let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
            domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
            this.currentContainerIndex = clickedContainerIndex;
            domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
            currentThumbnailIndex = clickedThumbnailIndex;

            // Show the current focus
            domThumbnails.eq(currentThumbnailIndex).css('border-color', thumbnail_border_color);
            this.focusedThumbnailList[this.currentContainerIndex] = currentThumbnailIndex;
            this.scrollThumbnails();
            this.showDetails();
        }
    }

    escapeOfCode() {
        this.oDescriptionContainer.escapeOfCode();
    }

    // Take the next thumbnail
    arrowRight() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        currentThumbnailIndex = (currentThumbnailIndex + 1) % domThumbnails.length;
        domThumbnails.eq(currentThumbnailIndex).css('border-color', thumbnail_border_color);
        this.focusedThumbnailList[this.currentContainerIndex] = currentThumbnailIndex;
        this.scrollThumbnails();
        this.showDetails();
    }

    // Take the previous thumbail
    arrowLeft() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
        currentThumbnailIndex = (currentThumbnailIndex - 1 + domThumbnails.length) % domThumbnails.length;
        domThumbnails.eq(currentThumbnailIndex).css('border-color', thumbnail_border_color);
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

        domThumbnails.eq(currentThumbnailIndex).css('border-color', thumbnail_border_color);
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

        domThumbnails.eq(currentThumbnailIndex).css('border-color', thumbnail_border_color);
        this.scrollThumbnails();
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


class ObjThumbnailContainer {
    /**
     * <div class="thumbnail-container-block" id="container-block-1">
     *   <div class="thumbnail-container-title">Comedy</div>
     *   <div class="thumbnail-container" id="container-1">
     *   </div>
     *   <div class="thumbnail-container-space" id="container-space-1"></div>
     * </div>
     */
    constructor(title, defaultThumbnailIndex = 0) {
        this.title = title
        this.numberOfThumbnails = undefined;
        this.defaultThumbnailIndex = defaultThumbnailIndex;
        this.currentThumbnailIndex = undefined;
        this.thumbnailList = [];

        this.resetDom();
    }

    resetDom() {
        this.domThumbnailContainer = $("<div>", {
            class: "thumbnail-container",
            id: "container-{???}"
        });
        this.domThumbnailContainer.empty();
    }

    getDom() {
        return this.domThumbnailContainer;
    }

    getTitle() {
        return this.title;
    }

    getDefaultThumbnailIndex() {
        return this.defaultThumbnailIndex;
    }

    getThumbnail(thumbnailIndex) {
        return this.thumbnailList[thumbnailIndex];
    }

    /**
     * Builds up new DOM for ThumbnailContainer
     * Called from the ScrollSection after it was taken out from the history
     * In short, it is called when you click on ESC
     */
    buildUpDom() {
        this.resetDom();

        for (let thumbnailIndex = 0; thumbnailIndex < this.thumbnailList.length; thumbnailIndex++) {
            let objThumbnail = this.thumbnailList[thumbnailIndex];

            this.coreDomeBuild(thumbnailIndex, objThumbnail);
        }
    }

    /**
     * 
     * Add a new Thumbnail to the DOM
     * It is called at the beginning. 
     * In short, it is called when you click on ENTER
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
    addThumbnail(recordId, objThumbnail) {
        let thumbnailIndex = this.thumbnailList.length;
        this.thumbnailList.push(objThumbnail);

        this.coreDomeBuild(thumbnailIndex, objThumbnail);
    }

    /**
     * Buld up one Thumbnail
     * It is called from 'addThumbnail()' and from 'buildUpDom()'
     * This is a common part of creating Thumbnail
     * 
     * @param {*} thumbnailIndex 
     * @param {*} objThumbnail 
     */
    coreDomeBuild(thumbnailIndex, objThumbnail){
        let title_thumb = objThumbnail.getThumbnailTitle();
        let thumbnail_src = objThumbnail.getThumbnailImageSource();
        let extras = objThumbnail.getExtras();
        let level = extras["level"];

        let domThumbnail = $("<div>", {
            class: "thumbnail",
            id: "container-{???}-thumbnail-" + thumbnailIndex
        });
        let domThumbnailTextWrapper = $("<div>", {
            class: "thumbnail-text-wrapper",
        });
        let domThumbnailText = $("<div>", {
            class: "thumbnail-text",
            text: title_thumb
        });
        let domImg = $("<img>", {
            src: thumbnail_src,
            alt: "Image"
        });

        domThumbnailTextWrapper.append(domThumbnailText);
        domThumbnail.append(domThumbnailTextWrapper);

        // Add LEVEL RIBBON if necessary
        if(level && ( level == "series" || level =="remake" || level == "sequel" )){
            let domLevelRib = $("<div>",{
                class: "ribbon-level",
                level: level,
                text: get_translated_level(level)
            });
            domThumbnail.append(domLevelRib);
        }

        domThumbnail.append(domImg);

        // Play Progress Bar
        //
        // Progress bar needed if the recent_position is set (even if it is 0) => meaning, it is a media
        let recent_state = extras["recent_state"];
        if(recent_state != undefined && recent_state['recent_position'] != undefined){
            let recent_position = recent_state['recent_position'];
            
            // Create the Progress bar
            let domPlayProgressWrapper = $("<div>", {
                class: "thumbnail-play-progress-bar-wrapper"
            });
            let domPlayProgress = $("<div>", {
                class: "thumbnail-play-progress-bar"
            });
            domPlayProgressWrapper.append(domPlayProgress)
            domThumbnail.append(domPlayProgressWrapper);

            let progress_percentage;
            let net_start_time = extras["net_start_time"];
            let net_stop_time = extras["net_stop_time"];
            let full_time = extras["full_time"]; 

            // This media:
            // - has been played at least once
            // - and the recent_position is not 0
            // - and the recent_position is between the net play time
            //
            // full_time != null && full_time > 600 && 
            if(recent_state['start_epoch'] != undefined && recent_position != 0 && recent_position >= net_start_time && recent_position < net_stop_time){
                let full_time = extras["full_time"];

                progress_percentage = 100 * recent_position / full_time

            // This media has not been played or it was played, but just a very short time=>recent position is 0
            }else{
                progress_percentage = 0;
            }
            domPlayProgress.css('width', progress_percentage + '%');
            if(progress_percentage == 0){
                domPlayProgressWrapper.hide()
            }else{
                domPlayProgressWrapper.show()
            }
        }
        this.domThumbnailContainer.append(domThumbnail);
    }
}

class Thumbnail {

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

    constructor() {
        this.selection_fn = undefined;
        this.thumbnailDict = {
        };
    }

    setFunctionForSelection(function_for_selection) {
        this.function_for_selection = function_for_selection;
    }

    getFunctionForSelection() {
        if (this.function_for_selection) {
            return this.function_for_selection;
        } else {
            return undefined;
        }
    }

    setImageSources({ thumbnail_src = undefined, description_src = undefined }) {
        if (thumbnail_src != undefined) {
            this.thumbnailDict["thumbnail_src"] = thumbnail_src;
        }
        
        if (description_src != undefined) {
            this.thumbnailDict["description_src"] = description_src;
        }
    }

    setTitles({ main = undefined, thumb = undefined, history = undefined }) {
        if (main != undefined) {
            this.thumbnailDict["title"] = main;
        }

        if (thumb != undefined) {
            this.thumbnailDict["title_thumb"] = thumb;
        }

        if (history != undefined) {
            this.thumbnailDict["title_history"] = history;
        }
    }

    setTextCard({ storyline = undefined, lyrics = undefined }) {
        if (storyline != undefined) {
            this.thumbnailDict["storyline"] = storyline;
        }
        if (lyrics != undefined) {
            this.thumbnailDict["lyrics"] = lyrics;
        }
    }

    setCredentials({ directors = undefined, writers = undefined, stars = undefined, actors = undefined, voices = undefined, hosts = undefined, guests = undefined, interviewers = undefined, interviewees = undefined, presenters = undefined, lecturers = undefined, performers = undefined, reporters = undefined }) {
        this.thumbnailDict["credentials"] = {}
        if (directors != undefined && Array.isArray(directors)) {
            this.thumbnailDict["credentials"]["directors"] = directors;
        }
        if (writers != undefined && Array.isArray(writers)) {
            this.thumbnailDict["credentials"]["writers"] = writers;
        }
        if (stars != undefined && Array.isArray(stars)) {
            this.thumbnailDict["credentials"]["stars"] = stars;
        }
        if (actors != undefined && Array.isArray(actors)) {
            this.thumbnailDict["credentials"]["actors"] = actors;
        }
        if (voices != undefined && Array.isArray(voices)) {
            this.thumbnailDict["credentials"]["voices"] = voices;
        }
        if (hosts != undefined && Array.isArray(hosts)) {
            this.thumbnailDict["credentials"]["hosts"] = hosts;
        }
        if (guests != undefined && Array.isArray(guests)) {
            this.thumbnailDict["credentials"]["guests"] = guests;
        }
        if (interviewers != undefined && Array.isArray(interviewers)) {
            this.thumbnailDict["credentials"]["interviewers"] = interviewers;
        }
        if (interviewees != undefined && Array.isArray(interviewees)) {
            this.thumbnailDict["credentials"]["interviewees"] = interviewees;
        }
        if (presenters != undefined && Array.isArray(presenters)) {
            this.thumbnailDict["credentials"]["presenters"] = presenters;
        }
        if (lecturers != undefined && Array.isArray(lecturers)) {
            this.thumbnailDict["credentials"]["lecturers"] = lecturers;
        }
        if (performers != undefined && Array.isArray(performers)) {
            this.thumbnailDict["credentials"]["performers"] = performers;
        }
        if (reporters != undefined && Array.isArray(reporters)) {
            this.thumbnailDict["credentials"]["reporters"] = reporters;
        }
    }

    setExtras({ medium_path = undefined, download = undefined, length = undefined, full_time = undefined, net_start_time = undefined, net_stop_time = undefined, date = undefined, origins = undefined, genres = undefined, themes = undefined, level = undefined, recent_state = {}, rate = undefined, skip_continuous_play = undefined, tags = []}) {
        this.thumbnailDict["extras"] = {}

        // TODO: This is not the best choice to store 'medium_path' in the 'extras', but that is what I chose. It could be changed
        this.thumbnailDict["extras"]["medium_path"] = medium_path;

        // TODO: This is not the best choice to store 'download' in the 'extras', but that is what I chose. It could be changed
        this.thumbnailDict["extras"]["download"] = download;

        this.thumbnailDict["extras"]["length"] = length;

        this.thumbnailDict["extras"]["full_time"] = full_time;

        this.thumbnailDict["extras"]["net_start_time"] = net_start_time;

        this.thumbnailDict["extras"]["net_stop_time"] = net_stop_time;

        this.thumbnailDict["extras"]["date"] = date;

        this.thumbnailDict["extras"]["origins"] = origins;

        this.thumbnailDict["extras"]["genres"] = genres;

        this.thumbnailDict["extras"]["themes"] = themes;

        this.thumbnailDict["extras"]["level"] = level;

        this.thumbnailDict["extras"]["recent_state"] = recent_state;

        this.thumbnailDict["extras"]["rate"] = rate;

        this.thumbnailDict["extras"]["skip_continuous_play"] = skip_continuous_play;

        this.thumbnailDict["extras"]["tags"] = tags;
    }

    setExtrasRate(rate){
        this.thumbnailDict["extras"]["rate"] = rate;
    }

    removeExtrasTag(tag){
        let tag_list = this.thumbnailDict["extras"]["tags"];
        let filtered_list = tag_list.filter(filter_tag);

        this.thumbnailDict["extras"]["tags"] = filtered_list;

        function filter_tag(tg){
            return tg !== tag;
        }
    }

    addExtraTag(tag){
        let tag_list = this.thumbnailDict["extras"]["tags"];
        tag_list.push(tag);
        this.thumbnailDict["extras"]["tags"] = tag_list;
    }

    setAppendix(appendix_list) {
        this.thumbnailDict['appendix'] = appendix_list;
    }

    getThumbnailDict() {
        return this.thumbnailDict;
    }

    getThumbnailImageSource() {
        if ("thumbnail_src" in this.thumbnailDict)
            return this.thumbnailDict["thumbnail_src"];
        return "";
    }

    getDescriptionImageSource() {
        if ("description_src" in this.thumbnailDict)
            return this.thumbnailDict["description_src"];
        return "";
    }

    getTitle() {
        return this.thumbnailDict["title"];
        return "";
    }

    getThumbnailTitle() {
        if ("title_thumb" in this.thumbnailDict)
            return this.thumbnailDict["title_thumb"];
        return "";
    }

    getHistoryTitle() {
        if ("title_history" in this.thumbnailDict)
            return this.thumbnailDict["title_history"];
        return "";
    }

    getStoryline() {
        if ("storyline" in this.thumbnailDict)
            return this.thumbnailDict["storyline"];
        return ""
    }

    getLyrics() {
        if ("lyrics" in this.thumbnailDict)
            return this.thumbnailDict["lyrics"];
        return ""
    }

    getCredentials() {
        if ("credentials" in this.thumbnailDict)
            return this.thumbnailDict["credentials"];
        return {};
    }

    getExtras() {
        if ("extras" in this.thumbnailDict)
            return this.thumbnailDict["extras"];
        return {};
    }

    getAppendix() {
        if ("appendix" in this.thumbnailDict)
            return this.thumbnailDict["appendix"];
        return {};
    }
}


class ObjDescriptionContainer {
    constructor(objScrollSection) {
        this.description_img = {
            width: 0,
            height: 0
        }
        this.objThumbnailController = undefined;
        this.objScrollSection = objScrollSection;
    }

    setThumbnailController(objThumbnailController) {
        this.objThumbnailController = objThumbnailController;
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
    refreshDescription(thumbnail, card_id, fileName, title, storyline, lyrics, credentials, extra, appendix_list) {
        let mainObject = this;
        let descImg = new Image();
        mainObject.card_id = card_id;
        mainObject.thumbnail = thumbnail;
        descImg.src = fileName;

        // when the image loaded, the onload event will be fired
        descImg.onload = function (refToObjThumbnailController) {
            let refToThis = this;
            return function () {

                // calculates the new size of the description image
                mainObject.description_img.height = descImg.height;
                mainObject.description_img.width = descImg.width;

                // -------------
                // --- title ---        
                // -------------
                let descTextTitle = $("#description-text-title");
                descTextTitle.empty();
                descTextTitle.html(title);

                // TODO: probably it should be renamed to #description-text-main-area
                let descTextStoryline = $("#description-text-storyline");
                descTextStoryline.empty();

                if (storyline) {

                    // -----------------
                    // --- storyline ---        
                    // -----------------
                    descTextStoryline.html(storyline);

                } else if (lyrics) {
                    // --------------
                    // --- lyrics ---        
                    // --------------
                    descTextStoryline.html(lyrics);

                } else{
                    // -------------
                    // --- empty ---        
                    // -------------

                    descTextStoryline.html("");
                }

                // -----------------

                // -------------
                // --- extra ---
                // -------------

                //
                // --- extra - year ---
                //
                let descTextExtraDate = $("#description-text-extra-date");
                descTextExtraDate.empty();
                let textExtraDate = "";
                if ("date" in extra && extra["date"]) {
                    textExtraDate += "" + extra["date"] + "";
                }
                descTextExtraDate.html(textExtraDate);

                //
                // --- extra - length ---
                //
                let descTextExtraLength = $("#description-text-extra-length");
                descTextExtraLength.empty();
                let textExtraLength = "";
                if ("length" in extra && extra["length"]) {
                    textExtraLength += "   ";
                    textExtraLength += extra["length"];
                }
                descTextExtraLength.html(textExtraLength);

                //
                // --- extra - origin ---
                //
                let descTextExtraOrigin = $("#description-text-extra-block-origin");
                descTextExtraOrigin.empty();
                let textExtraOrigin = "";
                if ("origins" in extra && extra["origins"]) {
                    let originList = extra["origins"];
                    let first = true;
                    for (let item of originList) {
                        if (first) {
                            first = false;
                        } else {
                            textExtraOrigin += " • ";
                        }
                        textExtraOrigin += item;
                    }
                }
                descTextExtraOrigin.html(textExtraOrigin);

                //
                // --- extra - genre ---
                //
                let descTextExtraGenre = $("#description-text-extra-block-genre");
                descTextExtraGenre.empty();
                let textExtraGenre = "";
                if ("genres" in extra && extra["genres"]) {
                    let genreList = extra["genres"];
                    let first = true;
                    for (let item of genreList) {
                        if (first) {
                            first = false;
                        } else {
                            textExtraGenre += " • ";
                        }
                        textExtraGenre += item;
                    }
                }
                descTextExtraGenre.html(textExtraGenre);

                //
                // --- extra - theme ---
                //
                let descTextExtraTheme = $("#description-text-extra-block-theme");
                descTextExtraTheme.empty();
                let textExtraTheme = "";
                if ("themes" in extra && extra["themes"]) {
                    let themeList = extra["themes"];
                    let first = true;
                    for (let item of themeList) {
                        if (first) {
                            first = false;
                        } else {
                            textExtraTheme += " • ";
                        }
                        textExtraTheme += item;
                    }
                }
                descTextExtraTheme.html(textExtraTheme);







                //
                // --- extra - tagging ---
                //
                let descTagging = $("#description-tagging");
                descTagging.empty();

                if(extra["medium_path"]){

                    // Construct + button
                    let tagButton = $('<div>', {
                        id: 'description-tagging-add',
                        class: "description-tagging-button"
                    });
                    let tagButtonText = $('<span>', {
                        class: "description-tagging-button-add",
                        //➕
                        text: "  \u{2795}  "
                    });
                    tagButton.append(tagButtonText);
                    descTagging.append(tagButton);

                    // Construct TAG buttons
                    for (let i = 0; i < extra["tags"].length; i++ ){  
                        let tag_name = extra["tags"][i];
                        let hash = tag_name.hashCode();
                        let tagButton = $('<div>', {
                            id: 'description-tagging-' + hash,
                            class: "description-tagging-button"
                        });
                        let tagButtonText = $('<span>', {
                            class: "description-tagging-button-text",
                            text: tag_name
                        });
                        let tagButtonClose = $('<span>', {
                            class: "description-tagging-button-close",
                            //🗙❌
                            text: '\u{274C}' , 
                            tag_name: tag_name,
                            hash: hash
                        });
                        tagButton.append(tagButtonText);
                        tagButton.append(tagButtonClose);

                        descTagging.append(tagButton);
                    }

                    // 'Add TAG' listener
                    tagButtonText.on("click", function() {
                        
                        // Disable the global key event listener
                        let orig_focus_task = refToObjThumbnailController.focusTask
                        refToObjThumbnailController.focusTask = FocusTask.Text;
                        
                        tagButton.hide(); // Hide the + button

                        // Create text field
                        let textField = $('<input>', {
                            type: 'text',
                            class: 'description-tagging-field',
                        });
                        // put the text field in the first position
                        descTagging.prepend(textField); // Add text field
                        
                        // Focus on the text field
                        textField.focus();

                        // Event for when the text field loses focus
                        textField.on('blur', function() {
                            textField.remove();     // Remove text field
                            tagButton.show();       // Show the + button again

                            // Enable the global key event listener
                            refToObjThumbnailController.focusTask = orig_focus_task;
                        });

                        // Event for ENTER key press on the field
                        //textField.on('keypress', function(e) {
                        textField.on('keydown', function(e) {

                            // Stop probageating keydown to up
                            e.stopPropagation()

                            // If you clicked ENTER on the text
                            if (e.key === 'Enter') {
                                let tag_name = textField.val().trim();
                                if (tag_name !== "") {
                                    let hash = tag_name.hashCode();

                                    // Add the tag from the DB
                                    let rq_method = "POST";
                                    let rq_url = "http://" + host + port + "/personal/tag/insert";
                                    let rq_assync = false;
                                    let rq_data = {"card_id": card_id, "name": tag_name}
                                    let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data });

                                    // If the removal was successful
                                    if(response.status == 200 && response.responseJSON["result"]){
                                        
                                        // Show the tag from the screen
                                        let tagButton = $('<div>', {
                                        id: 'description-tagging-' + hash,
                                        class: "description-tagging-button"
                                        });
                                        let tagButtonText = $('<span>', {
                                            class: "description-tagging-button-text",
                                            text: tag_name
                                        });
                                        let tagButtonClose = $('<span>', {
                                            class: "description-tagging-button-close",
                                            //🗙❌
                                            text: '\u{274C}' , 
                                            tag_name: tag_name,
                                            hash: hash
                                        });
                                        tagButton.append(tagButtonText);
                                        tagButton.append(tagButtonClose);
                                        descTagging.append(tagButton);

                                        //
                                        // Add the tag to the hierarchy for ALL Thumbnails in all ThumbnailContainer
                                        //
                                        for (let containerIndex = 0; containerIndex < mainObject.objScrollSection.thumbnailContainerList.length; containerIndex++) {

                                            let objThumbnailContainer = mainObject.objScrollSection.thumbnailContainerList[containerIndex];
                                            let thumbnailList = objThumbnailContainer.thumbnailList
                                            for (let thumbnailIndex = 0; thumbnailIndex < thumbnailList.length; thumbnailIndex++){
                                                let thumbnail = objThumbnailContainer.getThumbnail(thumbnailIndex);
                                            
                                                let single = thumbnail.function_for_selection.single;
                                                if("medium_dict" in single){
                                                    let other_card_id = single.medium_dict["card_id"];
                                                
                                                    if(other_card_id == card_id){
                                                    
                                                        thumbnail.addExtraTag(tag_name);

                                                    }                                    
                                                }
                                            }
                                        }
                                    }
                                }

                                // Trigger blur event to hide text field
                                textField.blur();

                            // If you clicked ESC on the field
                            }else if(e.key === "Escape"){

                                // Trigger blur event to hide text field
                                textField.blur();
                            }
                        });
                    });

                    // 'Remove TAG' listener
                    $(".description-tagging-button-close").on("click", function() {

                        // Remove the tag from the DB
                        let tag_name = $(this).attr('tag_name')
                        let rq_method = "DELETE";
                        let rq_url = "http://" + host + port + "/personal/tag/delete";
                        let rq_assync = false;
                        let rq_data = {"card_id": card_id, "name": tag_name}
                        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data });

                        // If the removal was successful
                        if(response.status == 200){

                            // Remove the tag from the screen
                            let hash = $(this).attr('hash')
                            $('#description-tagging-' + hash).remove()

                            //
                            // Remove the tag from the hierarchy for ALL Thumbnails in all ThumbnailContainer
                            //
                            for (let containerIndex = 0; containerIndex < mainObject.objScrollSection.thumbnailContainerList.length; containerIndex++) {
                                // console.log("container: " + containerIndex);

                                let objThumbnailContainer = mainObject.objScrollSection.thumbnailContainerList[containerIndex];
                                let thumbnailList = objThumbnailContainer.thumbnailList
                                for (let thumbnailIndex = 0; thumbnailIndex < thumbnailList.length; thumbnailIndex++){
                                    let thumbnail = objThumbnailContainer.getThumbnail(thumbnailIndex);

                                    let single = thumbnail.function_for_selection.single;
                                    if("medium_dict" in single){
                                        let other_card_id = single.medium_dict["card_id"];

                                        if(other_card_id == card_id){

                                            thumbnail.removeExtrasTag(tag_name);
                                        }                                    
                                    }
                                }
                            }
                        }
                    });
                }




                //
                // --- extra - rating ---
                //
                let descRating = $("#description-rating");
                descRating.empty();     // Clear any existing stars

                if(extra["medium_path"]){

                    let rate = extra["rate"];
                    let max_rate = 5;

                    //
                    // Generate the stars dynamically when the page loads
                    //
            
                    // Dynamically generate the star divs with img elements
                    for (let i = 1; i <= max_rate; i++) {
                        let starDiv = $('<div>', {
                            id: 'description-rating-' + i,
                            class: 'description-rating-rate'
                        });
            
                        let starImg = $('<img>', {
                            key: i,
                            src: 'images/rating/star-not-selected.png' // Initially set to 'not-selected'
                        });
            
                        starDiv.append(starImg);
                        descRating.append(starDiv);

                        if (i <= rate) {
                            $('#description-rating-' + i + ' img').attr('src', 'images/rating/star-selected.png');
                        } else {
                            $('#description-rating-' + i + ' img').attr('src', 'images/rating/star-not-selected.png');
                        }
                    }

                    //
                    // Handle hover effect
                    //
                    $('.description-rating-rate img').hover(function() {
                        //let index = $(this).index() + 1;
                        let imgSrc = $(this).attr('src');
                
                        // Change focus images on hover
                        if (imgSrc.includes('star-selected')) {
                            $(this).attr('src', 'images/rating/star-selected-focus.png');
                        } else {
                            $(this).attr('src', 'images/rating/star-not-selected-focus.png');
                        }
                    }, function(){
                        //let index = $(this).index() + 1;
                        let imgSrc = $(this).attr('src');
                
                        // Reset images on mouse leave
                        if (imgSrc.includes('star-selected-focus') || imgSrc.includes('star-selected')) {
                            $(this).attr('src', 'images/rating/star-selected.png');
                        } else {
                            $(this).attr('src', 'images/rating/star-not-selected.png');
                        }
                    });

                    //
                    // Handle click to change rating
                    //
                    $('.description-rating-rate img').click(function() {
                        //let index = $(this).index() + 1; // Get the clicked star index
                        let index = parseInt($(this).attr('key'));
                
                        // Three scenarios:
                        if (index > rate) {
                            // 1. Image was 'not selected', select all to the left including this one
                            rate = index;
                        } else if (index === rate) {
                            // 2. Image was 'selected' and no more stars are selected on the right side, deselect this one
                            rate--;
                        } else {
                            // 3. Image was 'selected', deselect all on the right side but keep the left side
                            rate = index;
                        }
                
                        //
                        // Update the stars based on the new rate
                        //
                        for (let i = 1; i <= max_rate; i++) {
                            if (i <= rate) {
                                $('#description-rating-' + i + ' img').attr('src', 'images/rating/star-selected.png');
                            } else {
                                $('#description-rating-' + i + ' img').attr('src', 'images/rating/star-not-selected.png');
                            }
                        }

                        let rq_method = "POST";
                        let rq_url = "http://" + host + port + "/personal/rating/update";
                        let rq_assync = false;
                        let rq_data = {"card_id": card_id, "rate": rate}
                        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data });
                        
                        if(response.status == 200){

                            //
                            // Update the selected Rate for ALL Thumbnails in all ThumbnailContainer
                            //
                            for (let containerIndex = 0; containerIndex < mainObject.objScrollSection.thumbnailContainerList.length; containerIndex++) {
                                // console.log("container: " + containerIndex);

                                let objThumbnailContainer = mainObject.objScrollSection.thumbnailContainerList[containerIndex];
                                let thumbnailList = objThumbnailContainer.thumbnailList
                                for (let thumbnailIndex = 0; thumbnailIndex < thumbnailList.length; thumbnailIndex++){
                                    let thumbnail = objThumbnailContainer.getThumbnail(thumbnailIndex);

                                    let single = thumbnail.function_for_selection.single;
                                    if("medium_dict" in single){
                                        let other_card_id = single.medium_dict["card_id"];

                                        if(other_card_id == card_id){
                                            // console.log("  thumbnail: " + thumbnailIndex + ", card: " + card_id + ", rate: " + rate);

                                            thumbnail.setExtrasRate(rate);
                                        }                                    
                                    }
                                }
                            }
                        }
                        // response.responseText
                        // response.statusText; //OK
                        // response.responseText; //"{"result": true, "data": [], "error": null}"
                        // console.log('Rate value: ' + rate); // Print the current rate value

                    });
                }

                // -------------------
                // --- credentials ---
                // -------------------

                let descTextCredentials = $("#description-text-credentials");
                descTextCredentials.empty();

                let credTable = $("<table>", {
                    border: 0,
                    id: "description-text-credentials-table"
                });
                descTextCredentials.append(credTable);

                mainObject.printCredentals(credTable, credentials, "performers", translated_titles['performer'] + ":");
                mainObject.printCredentals(credTable, credentials, "directors", translated_titles['director'] + ":");
                mainObject.printCredentals(credTable, credentials, "writers", translated_titles['writer'] + ":");
                mainObject.printCredentals(credTable, credentials, "stars", translated_titles['star'] + ":");
                mainObject.printCredentals(credTable, credentials, "actors", translated_titles['actor'] + ":");
                mainObject.printCredentals(credTable, credentials, "voices", translated_titles['voice'] + ":");
                mainObject.printCredentals(credTable, credentials, "hosts", translated_titles['host'] + ":");
                mainObject.printCredentals(credTable, credentials, "guests", translated_titles['guest'] + ":");
                mainObject.printCredentals(credTable, credentials, "interviewers", translated_titles['interviewer'] + ":");
                mainObject.printCredentals(credTable, credentials, "interviewees", translated_titles['interviewee'] + ":");
                mainObject.printCredentals(credTable, credentials, "presenters", translated_titles['presenter'] + ":");
                mainObject.printCredentals(credTable, credentials, "lecturers", translated_titles['lecturer'] + ":");
                mainObject.printCredentals(credTable, credentials, "reporters", translated_titles['reporter'] + ":");

                let descAppendixDownload = $("#description-appendix-download");
                let descAppendixPlay = $("#description-appendix-play");
                descAppendixDownload.empty();
                descAppendixPlay.empty();

                // ------------------------------
                // --- Download media allowed ---
                // ------------------------------
                if ("download" in extra && extra["download"] == 1) {
                    let file_path = extra["medium_path"];

                    let link = $('<a/>', {
                        class: "description-appendix-download-button",
                        href: file_path,
                        download: "download",   // This is needed to download
                        text: title
                    });
                    descAppendixDownload.append(link);
                }

                // ----------------
                // --- Appendix ---
                // ----------------
                for (let i in appendix_list) {

                    // Unfortunately the Appendix, does not gives back the same structure as the Card
                    // So I have to convert it to be compatible a little bit in case of PLAY

                    let card_id = appendix_list[i]['id'];
                    let show = appendix_list[i]['show'];
                    let download = appendix_list[i]['download'];
                    let source_path = appendix_list[i]['source_path'];
                    let media_dict = appendix_list[i]['media'];
                    let title = appendix_list[i]['title'];

                    // Every media in the appendix, will be shown, one by one, as download button
                    if (download == 1) {
                        // Unicode Character: 📥
                        let title_with_icon = '\u{1F4E5}' + " " + appendix_list[i]['title'];

                        // Through the keys: mediaTypes: text/picture/ebook
                        Object.entries(media_dict).forEach(([media_type, medium]) => {

                            // I do not care about the type of the media, just want to download
                            let file_path = pathJoin([source_path, "media", medium]);

                            let link = $('<a/>', {
                                    class: "description-appendix-download-button",
                                    href: file_path,
                                    download: "download",   // This is needed to download
                                    text: title_with_icon
                            });
                            descAppendixDownload.append(link);
                        });
                    }

                    // TODO: rename "show" to "play"
                    // Every media in the appendix, will be shown, one by one, as show/play button except the media_type=picture
                    // All media with media_type=picture in one appendix will be shown as ONE show/play button
                    if (show == 1) {
                        // Unicode Character: 25B6 ▶, 23EF ⏯, 
                        let title_with_icon = '\u{25B6}' + " " + appendix_list[i]['title'];

                        // Through the keys: mediaTypes: text/picture/ebook
                        Object.entries(media_dict).forEach(([media_type, medium]) => {

                                // The following structure tries to pretend it was a Card
                                let hit = {}
                                hit["media_type"] = media_type;
                                hit["id"] = card_id;
                                hit["source_path"] = source_path;
                                hit["title_req"] = title;
                                hit["title_orig"] = title;
                                let key = media_type;
                                let value = [medium];
                                hit["medium"] = {};
                                hit["medium"][key] = value;
                                hit["is_appendix"] = true;
                                let medium_dict = refToObjThumbnailController.getMediumDict(hit);

                                let link = $('<a/>', {
                                    class: "description-appendix-play-button",
                                    text: title_with_icon
                                });
                                link.click(function (my_medium_dict) {
                                    return function () {
                                        refToObjThumbnailController.playAppendixMedia(my_medium_dict);
                                    }
                                }(medium_dict));
                                descAppendixPlay.append(link);
                        });
                    }
                }

                // -------------------

                // Resizes the description section according to the size of the description image
                mainObject.resizeDescriptionSection();

            }

        }(this.objThumbnailController);

        // Loads the new image, which will trigger the onload event
        let description_image = "url(" + descImg.src + ")";
        t.style.setProperty('--description-image', description_image);
    }


    escapeOfCode() {
        // Trigger a click on the close icon
        $('#close-button').trigger('click');

        // remove the listener on the close icon
        $('#close-button').off('click');
    }


    /**
    * It resizes the description image and the description text wrapper (in the CSS) according to the available place
    * It is called when the size of the description section changed
    * Typically used by the ResizeObserver
    * 
    */
    resizeDescriptionSection() {
        let domDescriptionSectionDiv = $("#description-section");

        let domDescriptionImageDiv = $("#description-image");
        let description_image_border_sum_width = domDescriptionImageDiv.outerWidth() - domDescriptionImageDiv.innerWidth();
        let description_image_border_sum_height = domDescriptionImageDiv.outerHeight() - domDescriptionImageDiv.innerHeight();

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
        let domDescriptionAppendix = $("#description-appendix");
        let appendixHeight = domDescriptionAppendix.outerHeight();
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
        let storylineHeight = textWrapperHeight - titleHeight - extraHeight - appendixHeight - areaHeightBorder;

        t.style.setProperty('--description-text-storyline-height', storylineHeight + 'px');
        t.style.setProperty('--description-text-credentials-height', storylineHeight + 'px');
    }

    printCredentals(table, dict, id, title) {
        if (id in dict) {
            let first = true;
            let listItems = dict[id];
            for (let item of listItems) {
                let line = $("<tr>");
                let column = $("<td>");
                if (first) {
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


class History {
    constructor() {
        this.levelList = [];
    }

    addNewLevel(objScrollSection) {
        let text = objScrollSection.getFocusedThubnailContainerTitle();
        this.levelList.push({ "text": text, "obj": objScrollSection });
    }

    getLevels() {
        let text = "";
        let link = "";

        for (let i = 0; i < this.levelList.length - 1; i++) {
            text += this.levelList[i]["text"] + " >&nbsp;";
        }

        link = this.levelList.length ? " " + this.levelList[this.levelList.length - 1]["text"] : "";
        return { "text": text, "link": link };

    }

    popLevel() {
        if (this.levelList.length) {
            let level = this.levelList.pop();
            return level["obj"];
        } else {
            return undefined;
        }
    }
}


class FocusTask {
    static Menu = new FocusTask('menu');
    static Player = new FocusTask('player');
    static Dia = new FocusTask('dia');
    static Text = new FocusTask('text');
    static Pdf = new FocusTask('pdf');
    static Code = new FocusTask('code');
    static Picture = new FocusTask('picture');
    static Modal_Continue_Play = new FocusTask('modal_continue_play');
    constructor(name) {
        this.name = name
    }
}


class ThumbnailController {

    constructor(mainMenuGenerator) {
        this.language_code = mainMenuGenerator.language_code;
        this.history = new History();
        this.focusTask = FocusTask.Menu;
        this.updateMediaHistoryIntervalId = null;
        this.media_history_start_epoch = null;
       
        this.objScrollSection = new ObjScrollSection({ oContainerGenerator: mainMenuGenerator, objThumbnailController: this });

        let tshl = $("#history-section-link");
        tshl.click(function () {
            let esc = $.Event("keydown", { keyCode: 27 });
            $(document).trigger(esc);
        });
    }

    /*
    After the size of the description-section changed, the description-image size recalculation is needed.

    */
    resizeDescriptionSection() {
        //this.objScrollSection.focus();
        this.objScrollSection.getDescriptionContainer().resizeDescriptionSection();
    }

    getScrollSection() {
        return this.objScrollSection;
    }

    generateScrollSection(oContainerGenerator, historyLevels = { text: "", link: "" }) {
        let oScrollSection = new ObjScrollSection({ oContainerGenerator: oContainerGenerator, historyLevels: historyLevels, objThumbnailController: this });
//        oScrollSection.focusDefault();
        return oScrollSection;
    }

    enter(event) {

        if (this.focusTask === FocusTask.Menu) {

            // fetch the generator function of the thumbnail in the focus
            let functionForSelection = this.objScrollSection.getSelectedThumbnalFunctionForSelection();
            let functionContinuous = functionForSelection["continuous"]
            let functionSingle = functionForSelection["single"]

            // If the selected thumbnail will produce a sub-menu
            if ("menu" in functionSingle) {

                this.focusTask = FocusTask.Menu;

                // We get one level deeper in the history
                this.history.addNewLevel(this.objScrollSection);

                // take the generator's function
                let getGeneratorFunction = functionSingle["menu"];

                // and call the generator's function to produce a new Container Generator
                let oContainerGenerator = getGeneratorFunction();

                // Shows the new ScrollSection generated by the Container Generator
                this.objScrollSection = this.generateScrollSection(oContainerGenerator, this.history.getLevels());

            } else if ("audio" in functionSingle || "video" in functionSingle) {

                let play_list = []

                // If continuous play needed
                for (let hit of functionContinuous) {

                    play_list.push(this.getMediumDict(hit));
                }

console.log("before playmediaaudiovideo first elemenet: " + play_list[0]["title"]);

                this.playMediaAudioVideo(play_list);

            } else if ("picture" in functionSingle) {
                let medium_dict = functionSingle["medium_dict"];
                this.playMediaPicture(medium_dict);

            } else if ("pdf" in functionSingle) {
                let medium_dict = functionSingle["medium_dict"];
                this.playMediaPdf(medium_dict);

            } else if ("txt" in functionSingle) {
                let medium_dict = functionSingle["medium_dict"];                
                this.playMediaText(medium_dict);

            } else if ("code" in functionSingle) {
                let medium_dict = functionSingle["medium_dict"];                
                this.playMediaCode(medium_dict);
            }
        }
    }

    /*
    Generates the actual media_dict for the player_list
    */
    getMediumDict(hit){
                       
        let media;
        let medium_dict = {};
        let screenshot_path = null;
        
        if(!hit["is_appendix"]){
            screenshot_path = RestGenerator.getRandomScreenshotPath(hit["source_path"]);
        }

        let media_type = Object.keys(hit["medium"])[0]
          
        // if picture
        if( media_type == "picture" ){
            media = hit["medium"][media_type][0]
            medium_dict["medium_path_list"] = [pathJoin([hit["source_path"], "media", media])];

        // otherwise
        }else{
            if (hit["medium"][media_type] != undefined && hit["medium"][media_type].length > 0) {
                media = hit["medium"][media_type][0]
                medium_dict["medium_path"] = pathJoin([hit["source_path"], "media", media]);

            // if the actual card is a level, then it is not possible to play (in the ist)
            }else{
                medium_dict["medium_path"] = null
            }
        }   

        medium_dict["media_type"] = media_type;
        medium_dict["screenshot_path"] = screenshot_path,
        medium_dict["medium"] = hit["medium"];
        medium_dict["card_id"] = hit["id"];
        medium_dict["title"] = RestGenerator.getMainTitle(hit)
        medium_dict["net_start_time"] = hit["net_start_time"];
        medium_dict["net_stop_time"] = hit["net_stop_time"];
        medium_dict["full_time"] = hit["full_time"];

        return medium_dict;            
    }


    // ---

    // Play Appendix Media
    playAppendixMedia(medium_dict){
        let media_type = medium_dict["media_type"];
        
        if(media_type == "audio" || media_type == "video"){
            this.playMediaAudioVideo([medium_dict]);
        }else if(media_type == "pdf"){
            this.playMediaPdf(medium_dict);
        }else if(media_type == "picture"){
            this.playMediaPicture(medium_dict);
        }else if(media_type == "text"){
            this.playMediaText(medium_dict)
        }else if(media_type == "code"){
            this.playMediaCode(medium_dict)
        }
    }





























//    // Show the modal when the event is triggered
//    showModal() {
//        $('#playback-modal').fadeIn();
//
//        // Add a keydown listener to prevent keypress propagation when the modal is open
//        $(document).on('keydown.modal', function(e) {
//            console.log(e.key);
//            e.stopPropagation();
//            if (e.key === "Escape") {
//                $('#playback-modal').fadeOut(); // Hide modal if ESC is pressed
//            }
//        });
//    }
//    
//    // Hide the modal
//    hideModal() {
//      $('#playback-modal').fadeOut();
//
//      // Remove the modal-specific keydown event listener
//      $(document).off('keydown.modal');
//    }
    

    
    





closeModal(refToThis) {
    $('#continue-btn').off('click');
    $('#start-over-btn').off('click');
    $('.modal-content .close').off('click');
    $('#playback-modal').fadeOut();
    refToThis.focusTask = refToThis.originalTask;
}




    playMediaAudioVideo(continuous_list){
        
console.log("length continuous_list in the playMedia: " + continuous_list.length);

        // Takes the first element from the list
//        let medium_dict = continuous_list.shift();
        let medium_dict = continuous_list[0];

        let medium_path = medium_dict["medium_path"];
        let screenshot_path = medium_dict["screenshot_path"];
        let card_id = medium_dict["card_id"];
        let title = medium_dict["title"];
        let net_start_time = medium_dict["net_start_time"];
        let net_stop_time = medium_dict["net_stop_time"];
        let full_time = medium_dict["full_time"];

        let limit_days = 30;
        let refToThis = this;

        if (medium_path != null) {

            // REST request to check if the played media was interrupted - take it from the recent database, not from the thumbnail data
            let recent_position = refToThis.getMediaPositionInLatestHistory(card_id, limit_days)

            // The length of the media >= 10 minutes and Recent Position is between the Net Play interval then I handle the continuous play
            // full_time != null && full_time > 600 && 
            if (recent_position != null && (recent_position < net_stop_time) && (recent_position >= net_start_time) && recent_position != 0){

//                refToThis.originalTask = refToThis.focusTask;
//                refToThis.focusTask = FocusTask.Modal_Continue_Play;
//
///*                $(document).on('keydown.modal', function(e) {
//                    console.log(e.key);
//                    e.stopPropagation();
//                    if (e.key === "Escape") {
//                        $('#playback-modal').fadeOut();
//                        refToThis.focusTask = refToThis.originalTask;
//                    }
//                });
//*/                
//
//                // Message in the modal window
//                $("#playback-modal .modal-content p").html("Playback of this media was interrupted last time.<br> Would you like to resume playback or start from the beginning?");
//
//                //this.showModal()
//                $('#playback-modal').fadeIn();
//
//                // Delay focusing to avoid immediate Enter trigger
//                setTimeout(function () {
//                    $('#continue-btn').focus(); // Set initial focus to the first button
//                }, 100); // Adjust delay as needed
//
//                // Handle button clicks
//                $('#continue-btn').on('click', function (e) {
//                    refToThis.closeModal(refToThis);
//
//console.error("!!!! size: " + continuous_list.length + ", title: " + continuous_list[0]["title"]);
//
//                    refToThis.configurePlayer(refToThis, continuous_list, recent_position);
//                    
//                });
//
//                $('#start-over-btn').on('click', function (e) {
//                    refToThis.closeModal(refToThis);
//                    recent_position = 0;
//                    refToThis.configurePlayer(refToThis, continuous_list, recent_position);
//                });
//
//                // Handle close button click
//                $('.modal-content .close').on('click', function (e) {
//                    refToThis.closeModal(refToThis);
//                });
//  
//
//                let buttons = $('.focusable');
//                let currentFocusIndex = 0;
////                buttons.eq(currentFocusIndex).focus();
//
//                buttons.on('keydown', function (e) {
//                  if (e.key === "ArrowRight" || e.key === "Tab") {
//                    e.preventDefault();
//                    currentFocusIndex = (currentFocusIndex + 1) % buttons.length;
//                    buttons.eq(currentFocusIndex).focus();
//                  } else if (e.key === "ArrowLeft") {
//                    e.preventDefault();
//                    currentFocusIndex = (currentFocusIndex - 1 + buttons.length) % buttons.length;
//                    buttons.eq(currentFocusIndex).focus();
//                  } else if (e.key === "Enter") {
//                    buttons.eq(currentFocusIndex).click();
//                  }
//                });

                // Disable keys behind the Dialog()
                refToThis.originalTask = refToThis.focusTask;
                refToThis.focusTask = FocusTask.Modal_Continue_Play;

                // Wait 200ms before I show the Dialog(), otherwise, the Enter, which triggered this method, would click on the first button on the Dialog(), close the Dialog and start the play
                setTimeout(() => {
                    $("#dialog-confirm-continue-interrupted-play p").html("Playback of this media was interrupted last time.<br> Would you like to resume playback or start from the beginning?");
                    $("#dialog-confirm-continue-interrupted-play").dialog({
                        //closeOnEscape: false,
                        resizable: false,
                        height: "auto",
                        width: 400,
                        modal: true,
                        zIndex: 1100,
                        title: "Interrupted playback",                    
                        // beforeClose: function( event, ui ) {
                        //     setTimeout(function () {      
                        //         refToThis.focusTask = refToThis.originalTask;
                        //      }, 500);

                        // },
                        buttons: {
                          "Continue": function() {
                            $( this ).dialog( "close" );
                            refToThis.configurePlayer(refToThis, continuous_list, recent_position);                       
                          },
                          "From beginning": function() {
                            $( this ).dialog( "close" );
                            recent_position = 0;
                            refToThis.configurePlayer(refToThis, continuous_list, recent_position);
                          }
                        },

                        open: function() {
                            const buttons = $(this).parent().find(".ui-dialog-buttonset button");
                            let focusedButtonIndex = 0;

                            $(document).on("keydown.arrowKeys", function(event) {
                              if (event.key === "ArrowRight") {
                                focusedButtonIndex = (focusedButtonIndex + 1) % buttons.length;
                                buttons.eq(focusedButtonIndex).focus();
                                event.preventDefault();
                              } else if (event.key === "ArrowLeft") {
                                focusedButtonIndex = (focusedButtonIndex - 1 + buttons.length) % buttons.length;
                                buttons.eq(focusedButtonIndex).focus();
                                event.preventDefault();
                              }
                            });

                            $(this).parent().find(".ui-dialog-buttonpane button:first").focus();
                          },
                          close: function() {
                            $(document).off("keydown.arrowKeys"); // Remove listener on close

                            setTimeout(function () {      
                                refToThis.focusTask = refToThis.originalTask;
                            }, 500);

                            $(this).dialog("destroy");
                          },
                    });
                }, 200);




                console.error("myerror");


            // Otherwise it starts to play from the beginning
            }else{
                recent_position = 0;
                this.configurePlayer(refToThis, continuous_list, recent_position);
            }
        }
    }





    /**
     * 
     * @param {*} refToThis 
     * @param {*} continuous_list - Still contains the recent playing media - first element
     * @param {*} recent_position 
     */
    configurePlayer(refToThis, continuous_list, recent_position){

        let medium_dict = continuous_list[0];

        let medium_path = medium_dict["medium_path"];
        let screenshot_path = medium_dict["screenshot_path"];
        let card_id = medium_dict["card_id"];
        let title = medium_dict["title"];

console.error("!!! " + title);

        let net_start_time = medium_dict["net_start_time"];
        let net_stop_time = medium_dict["net_stop_time"];

        let player = $("#video_player")[0];

        // Remove all media source from the player befor I add the new
        $('#video_player').children("source").remove();

        // Creates a new source element
        let newSourceElement = $('<source>');
        newSourceElement.attr('src', medium_path);

        $('#video_player').append(newSourceElement);


//            let isInFullScreen = false;
//            if (document.fullscreenEnabled){
//                player.requestFullscreen();
//
//                isInFullScreen = (document.fullScreenElement && document.fullScreenElement !== null) ||  (document.mozFullScreen || document.webkitIsFullScreen);
//            }
//            console.log("fullscreen: " + isInFullScreen);

        if (player.requestFullscreen) {
            player.requestFullscreen();
        }else if (player.msRequestFullscreen) {
            player.msRequestFullscreen();
        } else if (player.mozRequestFullScreen) {
            player.mozRequestFullScreen();
        } else if (player.webkitRequestFullscreen) {
            player.webkitRequestFullscreen();
        }

        if( screenshot_path != null){
            player.poster = screenshot_path;
        }else{
            player.poster = "";
        }

// this part works together with startPlayer() and pausePlayer() 
// Using this, instead of just player.play() and player.pause() prevent to get 'The play() request was interrupted by a call to pause()" error' error
// The below code is a temporary solution. I kept it to learn:
//        setTimeout(function () {      
//            player.play();
//         }, 550);
//        player.play();

this.isPlaying = false;

// On video playing toggle values
player.onplaying = function() {
    this.isPlaying = true;
};

// On video pause toggle values
player.onpause = function() {
    this.isPlaying = false;
};

player.controls = true;
player.autoplay = true;
player.currentTime = recent_position;
player.load();
this.startPlayer()

// ---

        // REST request to register this media in the History
        this.media_history_start_epoch = refToThis.registerMediaInHistory(card_id, recent_position);

        // ENDED event listener
        $("#video_player").bind("ended", function (par) {
            refToThis.finishedPlaying('ended', continuous_list);
        });

        // FULLSCREENCHANGE event listener
        $('#video_player').bind('webkitfullscreenchange mozfullscreenchange fullscreenchange', function (e) {
            var state = document.fullScreen || document.mozFullScreen || document.webkitIsFullScreen;

            // If exited of full screen
            if (!state) {
                refToThis.finishedPlaying('fullscreenchange', continuous_list);
            }
        });
        player.style.display = 'block';

        // It is important to have this line, otherwise you can not control the voice level, and the progress line will stay
        $('#video_player').focus();

        this.focusTask = FocusTask.Player;        
    }


// Using the below 2 functions, instead of just player.play() and player.pause() prevent to get 'The play() request was interrupted by a call to pause()" error' error
startPlayer(){
    let player = $("#video_player")[0];
    if( !player.paused && !this.isPlaying){
        return player.play();
    }
}
pausePlayer(){
    let player = $("#video_player")[0];
    if( !player.paused && this.isPlaying){
        return player.pause();
    }
}


    playMediaPdf(medium_dict){
        let medium_path = medium_dict["medium_path"];

        if (medium_path != null) {
            let retToThis = this;
            this.focusTask = FocusTask.Text;
            let fancybox_list = [];
            let opts = {
                // caption: media_path,
                thumb: medium_path,
                width: $(window).width(),
                afterShow: function (instance, current) { },
            }
            let src = medium_path;
            fancybox_list.push({
                src: src,
                opts: opts
            })
            $.fancybox.open(fancybox_list, {
                loop: false,
                fitToView: true,
                afterClose: function (instance, current) {
                    retToThis.focusTask = FocusTask.Menu;
                }
            });
        }    
    }


    // It can play list of pictures => medium_path = List
    playMediaPicture(medium_dict){
        let medium_path_list = medium_dict["medium_path_list"];

        if (medium_path_list != null) {
            let refToThis = this;
            this.focusTask = FocusTask.Player;
            let fancybox_list = [];
            for (let media_path of medium_path_list) {
                let opts = {
                    // caption: media_path,
                    thumb: media_path,
                    width: $(window).width(),
                    // fitToView: true,                            // does not work
                    // autoSize: true,                             // does not work
                    afterShow: function (instance, current) { },
                }
                let src = media_path;
                fancybox_list.push({
                    src: src,
                    opts: opts
                })
            }
            $.fancybox.open(fancybox_list, {
                loop: false,
                fitToView: true,
                afterClose: function (instance, current) {
                refToThis.focusTask = FocusTask.Menu;
                }
            });
        }
    }
    
    playMediaText(medium_dict){
        let medium_path = medium_dict["medium_path"];

        this.playMediaCode(medium_path);
    }

    playMediaCode(medium_dict){
        let medium_path = medium_dict["medium_path"];

        if (medium_path != null) {
            let retToThis = this;
            this.focusTask = FocusTask.Code;

            // Text load and show in a modal window

            $.ajax({
                url: medium_path,
                dataType: 'text',
                success: function (text) {
                    $('#text-content').text(text);
                    $('#modal, #overlay').show();

                    // Highlight.js initialization after modal is shown
                    hljs.highlightAll();
                },
                error: function (error) {
                    console.error('Error loading text file:', error);
                }
            });

            // Bezárás gomb eseménykezelő
            $('#close-button').on('click', function () {

                $('#modal').hide();
                $('#overlay').hide();

                $('#text-content').empty();
                $('#text-content').removeAttr("data-highlighted");

                retToThis.focusTask = FocusTask.Menu;
            });
        }        
    }


    /**
     * Come here when the recent media stopped playing
     * Make decision if the next media should be played, and start to play it if needed
     * 
     * @param {*} event 
     * @param {*} continuous_list - Still contains the recent playing media - first element
     */
    finishedPlaying(event, continuous_list) {

        // Take the first element of the list and remove it from the list
        let medium_dict = continuous_list.shift();

        // Stop updating the current media history
        if(this.updateMediaHistoryIntervalId != null){
            clearInterval(this.updateMediaHistoryIntervalId);
            console.log("Stopped Media History Interval. Id: " + this.updateMediaHistoryIntervalId);
        }

        let player = $("#video_player")[0];
        let domPlayer = $("#video_player");

        let card_id = medium_dict["card_id"];

        // Update the Current Position at the finished position
        if (this.media_history_start_epoch != null){            
            //let card_id = medium_dict["card_id"];
            this.updateMediaHistory(this.media_history_start_epoch, card_id)
        }

        // Refresh the Progress bar
        let recent_position = player.currentTime;
//        this.objScrollSection.refreshFocusedThumbnailProgresBar(recent_position)

//--

        //
        // Set the progressbar in the hierarchy for ALL Thumbnails in all ThumbnailContainer
        //
        for (let containerIndex = 0; containerIndex < this.objScrollSection.thumbnailContainerList.length; containerIndex++) {
        
            let domThumbnails = $('#container-' + containerIndex + ' .thumbnail');
            let objThumbnailContainer = this.objScrollSection.thumbnailContainerList[containerIndex];
            let thumbnailList = objThumbnailContainer.thumbnailList
            for (let thumbnailIndex = 0; thumbnailIndex < thumbnailList.length; thumbnailIndex++){
                let thumbnail = objThumbnailContainer.getThumbnail(thumbnailIndex);
            
                let single = thumbnail.function_for_selection.single;
                if("medium_dict" in single){
                    let other_card_id = single.medium_dict["card_id"];
                
                    if(other_card_id == card_id){
                    
                        let extras = thumbnail.getExtras();
                        let recent_state = extras["recent_state"];
                        let full_time = extras["full_time"]; 
                        let net_start_time = extras["net_start_time"];
                        let net_stop_time = extras["net_stop_time"];
                        
                        recent_state["recent_position"] = recent_position;
                        extras["recent_state"] = recent_state;
                        thumbnail.setExtras(extras);
                        
                        let progress_percentage;
                        // full_time != null && full_time > 600 && 
                        if(recent_position != 0 && recent_position >= net_start_time && recent_position < net_stop_time){
                            progress_percentage = 100 * recent_position / full_time;
                        }else{
                            progress_percentage = 0;
                        }
                        
                        let bar_wrapper = domThumbnails.eq(thumbnailIndex).find(".thumbnail-play-progress-bar-wrapper");
                        let bar = domThumbnails.eq(thumbnailIndex).find(".thumbnail-play-progress-bar")
                        
                        bar.css('width', progress_percentage + '%');
                        
                        if(progress_percentage == 0){
                            bar_wrapper.hide()
                        }else{
                            bar_wrapper.show()
                        }
                    }                                    
                }
            }
        }


//--

        // Remove the playing list
        domPlayer.children("source").remove();

        // if I'm here because the player 'ended' and there is at least 1 more element in the play_list
        if (event == 'ended' && continuous_list.length > 0) {

            this.objScrollSection.arrowRight()
            
            let medium_dict = continuous_list[0];
            let medium_path = medium_dict["medium_path"];
            let screenshot_path = medium_dict["screenshot_path"];
            let card_id = medium_dict["card_id"];
            let title = medium_dict["title"];

            // takes the next element until it is a media - skip the collections (series, sequels, ...)
            while(medium_path == null && continuous_list.length > 0){
                continuous_list.shift();
                medium_dict = continuous_list[0];
                medium_path = medium_dict["medium_path"];
                screenshot_path = medium_dict["screenshot_path"];
                card_id = medium_dict["card_id"];
                title = medium_dict["title"];
                
                // next focus on the thumbnails
                this.objScrollSection.arrowRight()
            }
           
            // if the recent element is media
            if(medium_path != null){
            
                // Creates a new source element
                let sourceElement = $('<source>');
                sourceElement.attr('src', medium_path);
                domPlayer.append(sourceElement);

                // Poster only if audio medium
                if ("audio" in medium_dict["medium"]) {
                    player.poster = screenshot_path;
                } else {
                    player.poster = "";
                }

                // REST request to register this media in the History
                this.media_history_start_epoch = this.registerMediaInHistory(card_id, 0);

                player.load();
                this.startPlayer()
                //player.play();

                // It is important to have this line, otherwise you can not control the voice level and the progress line will stay
                domPlayer.focus();

            }else{
                this.stop_playing(player, domPlayer, event);
            }

        // Stop playing manually or empty list
        } else {
            this.stop_playing(player, domPlayer, event);
        }
    }

    // No more media in the play list, I stop the play
    stop_playing(player, domPlayer, event){

        // Remove the listeners
        domPlayer.off('fullscreenchange');
        domPlayer.off('mozfullscreenchange');
        domPlayer.off('webkitfullscreenchange');
        domPlayer.off('ended');

        domPlayer.hide();

        this.pausePlayer()        
        //player.pause();

        player.height = 0;

        this.focusTask = FocusTask.Menu;

        if (event == 'fullscreenchange') {

        } else if (event == 'ended') {
            $('video')[0].webkitExitFullScreen();
        }

        player.load();
    }

    escape() {
        if (this.focusTask === FocusTask.Menu) {

            let oT = this.history.popLevel();
            if (oT) {
                this.objScrollSection = oT;
                this.objScrollSection.buildUpDom();
            }

        } else if (this.focusTask === FocusTask.Player) {
            this.focusTask = FocusTask.Menu;

        } else if (this.focusTask === FocusTask.Code) {
            this.objScrollSection.escapeOfCode();
        }
    }

    arrowLeft() {
        if (this.focusTask === FocusTask.Menu) {
            this.objScrollSection.arrowLeft();

        } else if (this.focusTask === FocusTask.Code) {
            this.objScrollSection.escapeOfCode();
        }
    }

    arrowUp() {
        if (this.focusTask === FocusTask.Menu) {
            this.objScrollSection.arrowUp();
        }
    }

    arrowRight() {
        if (this.focusTask === FocusTask.Menu) {
            this.objScrollSection.arrowRight();

        } else if (this.focusTask === FocusTask.Code) {
            this.objScrollSection.escapeOfCode();
        }
    }

    arrowDown() {
        if (this.focusTask === FocusTask.Menu) {
            this.objScrollSection.arrowDown();
        }
    }

    tab() {
        if (this.focusTask === FocusTask.Menu) {
            //this.objScrollSection.arrowDown();
        }
    }

    /**
     * POST REST request to register the recent media in the History
     */ 
    registerMediaInHistory(card_id, recent_position){
        
        let rq_method = "POST";
        let rq_url = "http://" + host + port + "/personal/history/update";
        let rq_assync = false;
        let rq_data = {"card_id": card_id, "recent_position": recent_position}
        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data })

        let response_dict = response.responseJSON;
        let result = response_dict['result']
        let data_dict = response_dict['data']
        let error = response_dict['error']

        // The user is logged in and the register was successful
        if(result){
            this.updateMediaHistoryIntervalId = setInterval(this.updateMediaHistory, 60000, data_dict['start_epoch'], card_id);
            console.log("Start Media History Interval for " + card_id + " car id. Interval id: "+ this.updateMediaHistoryIntervalId);
        }else{
            this.updateMediaHistoryIntervalId = null;
            console.log("Media History Interval did not start: " + error);
        }

        return data_dict['start_epoch'];
    }

    /**
     * POST REST request to update the recent media in the History
     * 
     * @param {*} refToThis 
     * @param {*} start_epoch 
     * @param {*} card_id 
     */
    updateMediaHistory(start_epoch, card_id){
        let player = $("#video_player")[0];
        let currentTimeInSeconds = player.currentTime;

        console.log("Update media history was called. start_epoch: " + start_epoch + ", card_id: " + card_id + ", recent_position: " + currentTimeInSeconds);

        let rq_method = "POST";
        let rq_url = "http://" + host + port + "/personal/history/update";
        let rq_assync = false;
        let rq_data = {"card_id": card_id, "recent_position": currentTimeInSeconds, "start_epoch": start_epoch}
        let result = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data })

        // let result_data = result.responseJSON;
        // console.log("  result_data: " + result_data);
    }


    // TODO: This method should be deleted and the normal query should take the recent_position
    getMediaPositionInLatestHistory(card_id, limit_days=30){
        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/personal/history/request";
        let rq_assync = false;
        let rq_data = {"card_id": card_id, "limit_records": "1", "limit_days": limit_days}
        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data })     
    
        let response_dict = response.responseJSON;
        let result = response_dict['result']
        let data_list = response_dict['data']

        // If the query was OK and there was 1 record
        if (result && data_list.length > 0){
            let result_dict = data_list[0]
            return result_dict['recent_position'];
        }else{
            return 0;
        }
    }
}

