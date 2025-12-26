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
     *       <div class="thumbnail-container-title">
     *         <div class="thumbnail-container-title">Kategoriák</div>
     *         <div class="thumbnail-container-control-section">  ➕  </div>
     *       </div>
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
        this.objThumbnailController = objThumbnailController;

        this.oDescriptionContainer = new ObjDescriptionContainer(this);
        this.oDescriptionContainer.setThumbnailController(objThumbnailController);

        this.resetDom();
        this.oContainerGenerator.produceContainers(this);
    }

    resetDom() {
        // Remove all elements from the <div id=scroll-section> and <div id=detail-text-title> and <div id=detail-image-div>
        this.domScrollSection = $("#scroll-section");
        this.domScrollSection.empty();

        // ! Not only the dom should be reset but
//        this.thumbnailContainerList=[]
//        this.numberOfContainers=0
//        this.focusedThumbnailList=[]
//        this.currentContainerIndex = -1;

        let tsht = $("#history-section-text");
        tsht.html(this.historyLevels["text"]);

        let tshl = $("#history-section-link");
        tshl.html(this.historyLevels["link"]);

        $("#container-controllers-add").hide();
    }

    /**
     * Builds up new DOM for ControllerSection after it was taken out from the history
     */
    buildUpDom() {
        this.resetDom();
        let refToThis = this;

        for (let containerIndex = 0; containerIndex < this.thumbnailContainerList.length; containerIndex++) {
            let thumbnailContainer = this.thumbnailContainerList[containerIndex];

            thumbnailContainer.buildUpDom();

            this.addCoreThumbnailContainerObject(thumbnailContainer, containerIndex);

        }

        this.domThumbnailContainerBlocks = $('#scroll-section .thumbnail-container-block');

        // Restore + icon visibility if this is a search container
        const containerType = this.oContainerGenerator.menu_dict?.container_type ?? "normal";

        // If the container_type == 'search' configured in card_menu.yaml
        if (containerType === "search") {
            $("#container-controllers-add").show();
        }

        this.focus();
    }

    /**
     * It was written when the card menu configuration was hard coded and this method was called after all thumbnail was added to the container.
     * Consequently if you add thumbnail to the container later, the click listener will be skipped to add, so you will be not able to click on the thumbnail
     * Plus even the Thumbnail's '<div> id=container-{???}' will not be substituted
     */
    addThumbnailContainerObject(thumbnailContainer) {

        let containerIndex = this.focusedThumbnailList.length;

        this.addCoreThumbnailContainerObject(thumbnailContainer, containerIndex);

        // The ids must be changed as the ObjThumbnailContainer class has no idea about the id here (in the ObjScrollSection)
        let currentThumbnailIndex = thumbnailContainer.getDefaultThumbnailIndex();
        this.focusedThumbnailList.push(currentThumbnailIndex);
        this.thumbnailContainerList.push(thumbnailContainer);
        this.numberOfContainers++;

        // this variable should be refreshed every time when a new thumbnail is added
        this.domThumbnailContainerBlocks = $('#scroll-section .thumbnail-container-block');

        // Inform the ThumbnailContainer that it was added to the ObjScrollSection
        thumbnailContainer.setParent(this, containerIndex);

        return containerIndex
    }

    addCoreThumbnailContainerObject(thumbnailContainer, containerIndex){
        let refToThis = this;

        // Gets the Thumbnail Container JQuery Element
        let domThumbnailContainer = thumbnailContainer.getDom();

        let domThumbnailContainerBlock = $('<div>', {
            class: "thumbnail-container-block",
            id: "container-block-" + containerIndex
        });

        let domThumbnailContainerTitleSection = $("<div>", {
            class: "thumbnail-container-title-section",
        });

        // Creates the Title JQuery element of the Thumbnail Container
        let domThumbnailContainerTitle = $("<div>", {
            class: "thumbnail-container-title",
            text: thumbnailContainer.getTitle()
        });

        let domThumbnailContainerControlSection = $("<div>", {
            class: "thumbnail-container-control-section",
        });

        // Thumbnail Container modifier/delete icons
        //let scroll_section = this.oContainerGenerator['menu_dict']['container_list'][containerIndex];
        //let dynamic_queried = this.oContainerGenerator.menu_dict.container_list[containerIndex].dynamic_queried ?? null;
        //let static_hard_coded = this.oContainerGenerator.menu_dict.container_list[containerIndex].static_hard_coded ?? null;
        //let dynamic_hard_coded = this.oContainerGenerator.menu_dict.container_list[containerIndex].dynamic_hard_coded ?? null;

        // No menu_dict if the thumbnail list is generated by next_level
        const container_list = this.oContainerGenerator.menu_dict?.container_list ?? []
        const randomizable = this.oContainerGenerator.menu_dict?.randomizable ?? false;

        /*
        Here is the logic how the randomize 🎲 icons are displayed
        */
        if (

            // there are more than 2 thumbnails in the recent thumbnail container
            thumbnailContainer.thumbnailList.length >= 0 &&
            (
                (
                    // the thumbnail list is generated by next_level
                    container_list.length == 0
                )
                ||
                (
                    // there are at least 1 thumbnail container
                    container_list.length >= 1 &&

                    // the recent thumbanil container configured explicitly to have randomize button
                    randomizable && (

                        // dynamic_queried which always has only 1 element in the list
                        'dynamic_queried' in container_list[0] ||

                        // the recent thumbnail container is dynamic_hard_coded
                        (containerIndex < container_list.length && 'dynamic_hard_coded' in container_list[containerIndex])
                    )
                )
            )
        ){

            let domThumbnailContainerControlSectionRandomize = $("<div>", {
                class: "thumbnail-container-control-section-randomize",
                text: "  \u{1F3B2}  ",
                css: { "font-size": "1.3em" }
            }); // 🎲

            // Add click listener on the delete icon
            domThumbnailContainerControlSectionRandomize.click(function () {
                refToThis.clickedOnRandomizeThumbnailContainer(thumbnailContainer, domThumbnailContainerBlock);
            });

            domThumbnailContainerControlSection.append(domThumbnailContainerControlSectionRandomize);
        }

        /*
        Here is the logic how the modifier/delete 🗑🖊 icons are displayed
        If the container_type == 'search'               - configured in card_menu.yaml
        And the container_list == 'dynamic_hard_coded   - configured in card_menu.yaml
        */
        const containerType = this.oContainerGenerator.menu_dict?.container_type ?? "normal";
        if (containerType === "search" && container_list && ((container_list.length == 1 && 'dynamic_hard_coded' in container_list[0]) || (container_list.length > 1 && containerIndex < container_list.length && 'dynamic_hard_coded' in container_list[containerIndex]))){

            let domThumbnailContainerControlSectionDelete = $("<div>", {
                class: "thumbnail-container-control-section-delete",
                text: "  \u{1F5D1}  "
            }); // 🗑
            // Add click listener on the delete icon
            domThumbnailContainerControlSectionDelete.click(function () {
                refToThis.clickedOnDeleteThumbnailContainer(thumbnailContainer, domThumbnailContainerBlock);

            });

            let domThumbnailContainerControlSectionEdit = $("<div>", {
                class: "thumbnail-container-control-section-edit",
                text: "  \u{1F58A}  "
            }); // 🖊️
            domThumbnailContainerControlSectionEdit.click(function () {
                refToThis.clickedOnEditThumbnailContainer(thumbnailContainer, domThumbnailContainerBlock);
            });

            domThumbnailContainerControlSection.append(domThumbnailContainerControlSectionDelete);
            domThumbnailContainerControlSection.append(domThumbnailContainerControlSectionEdit);
        }

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

        domThumbnailContainerTitleSection.append(domThumbnailContainerTitle);

        domThumbnailContainerTitleSection.append(domThumbnailContainerControlSection);

        domThumbnailContainerBlock.append(domThumbnailContainerTitleSection);

        domThumbnailContainerBlock.append(domThumbnailContainer);
        domThumbnailContainerBlock.append(domThumbnailContainerSpace);
        this.domScrollSection.append(domThumbnailContainerBlock);
    }

    getDescriptionContainer() {
        return this.oDescriptionContainer;
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
        if (!this.focusedThumbnailList || !this.focusedThumbnailList.length) {
            return{"continuous": {}, "single": {}};
        }

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
        let currentThumbnailIndex = this.focusedThumbnailList?.[this.currentContainerIndex];
        let thumbnailContainer = this.thumbnailContainerList?.[this.currentContainerIndex];

        if (currentThumbnailIndex === undefined || thumbnailContainer === undefined) {
            return;
        }

        let thumbnail = thumbnailContainer.getThumbnail(currentThumbnailIndex)
        if (!thumbnail) {
            return;
        }

        let card_id = null;
        const single = thumbnail.function_for_selection.single;
        if("medium_dict" in single){
            card_id = single.medium_dict["card_id"];
        }

        const image = thumbnail.getDescriptionImageSource();
        const title = thumbnail.getTitle();
        const storyline = thumbnail.getStoryline();
        const lyrics = thumbnail.getLyrics();
        const credentials = thumbnail.getCredentials();
        const extra = thumbnail.getExtras();
        const appendix = thumbnail.getAppendix();

        // Shows the actual Description
        this.oDescriptionContainer.refreshDescription(thumbnail, card_id, image, title, storyline, lyrics, credentials, extra, appendix);
    }


    /**
     * Randomizes the order of thumbnails within a thumbnail container while maintaining data consistency.
     *
     * This method is triggered when the user clicks the 🎲 (dice) icon on a container. It performs a complete
     * shuffle of thumbnails that involves three critical data structures that must stay synchronized:
     *
     * 1. DOM Elements: The visual thumbnail elements in the browser
     * 2. Data Array: The thumbnailList containing all thumbnail data (titles, images, progress, etc.)
     * 3. Focus Tracking: The focusedThumbnailList tracking which thumbnail has the red border
     *
     * The synchronization is crucial because:
     * - DOM position determines visual order and click detection
     * - Data array position determines which data is shown when a thumbnail is selected
     * - Focus tracking determines which thumbnail gets the red border and shows details
     *
     * @param {ObjThumbnailContainer} thumbnailContainer - The container object being randomized
     * @param {jQuery} domThumbnailContainerBlock - The DOM element of the container block
     */
    clickedOnRandomizeThumbnailContainer(thumbnailContainer, domThumbnailContainerBlock) {
        // Extract container index from DOM ID (e.g., "container-block-2" -> 2)
        let containerId = domThumbnailContainerBlock.attr('id');
        let containerIndex = parseInt(containerId.replace('container-block-', ''));

        // Get the DOM container and its thumbnail children
        let domContainer = $('#container-' + containerIndex);
        let domThumbnails = domContainer.children('.thumbnail');

        // Only randomize if there are multiple thumbnails
        if (domThumbnails.length > 1) {
            let refToThis = this;

            // STEP 1: Generate random shuffle order using Fisher-Yates algorithm
            // Create array [0, 1, 2, 3, ...] representing original positions
            let indices = Array.from({length: domThumbnails.length}, (_, i) => i);

            // Fisher-Yates shuffle: randomly swap elements to create new order
            // This ensures each possible permutation has equal probability
            for (let i = indices.length - 1; i > 0; i--) {
                let j = Math.floor(Math.random() * (i + 1));
                [indices[i], indices[j]] = [indices[j], indices[i]];
            }
            // After shuffle, indices might be [2, 0, 3, 1] meaning:
            // - Position 0 gets thumbnail that was originally at position 2
            // - Position 1 gets thumbnail that was originally at position 0, etc.

            // STEP 2: Reorder the data array to match the new shuffle order
            // This is critical: the data must follow the visual elements
            let originalThumbnailList = [...this.thumbnailContainerList[containerIndex].thumbnailList];
            for (let i = 0; i < indices.length; i++) {
                // Put the data from original position indices[i] into new position i
                this.thumbnailContainerList[containerIndex].thumbnailList[i] = originalThumbnailList[indices[i]];
            }

            // STEP 3: Reorder DOM elements to match the shuffle
            // Convert jQuery collection to array for easier manipulation
            let thumbnailsArray = domThumbnails.toArray();
            domContainer.empty(); // Remove all thumbnails from DOM

            // Re-add thumbnails in the new shuffled order
            indices.forEach(originalIndex => {
                domContainer.append(thumbnailsArray[originalIndex]);
            });

            // STEP 4: Update DOM IDs and restore click functionality
            // When we move DOM elements, they lose their event listeners and may have wrong IDs
            domContainer.children('.thumbnail').each(function (newIndex) {
                let thumbnailElement = $(this);

                // Update ID to reflect new position (needed for click detection)
                thumbnailElement.attr('id', 'container-' + containerIndex + '-thumbnail-' + newIndex);

                // Re-attach click listener (lost when DOM was manipulated)
                thumbnailElement.click(function () {
                    refToThis.clickedOnThumbnail($(this).attr('id'));
                });
            });

            // STEP 5: Update focus tracking to follow the moved thumbnail
            // If thumbnail at position 0 was focused and moved to position 3, focus should move to position 3
            let currentFocusedIndex = this.focusedThumbnailList[containerIndex];
            let newFocusedIndex = indices.indexOf(currentFocusedIndex);
            this.focusedThumbnailList[containerIndex] = newFocusedIndex;

            // STEP 7: Rebuild continuous play arrays based on new shuffled order
            for (let i = 0; i < this.thumbnailContainerList[containerIndex].thumbnailList.length; i++) {
                let thumbnail = this.thumbnailContainerList[containerIndex].thumbnailList[i];
                let functionForSelection = thumbnail.getFunctionForSelection();

                if (functionForSelection && functionForSelection.continuous) {
                    // Build new continuous array starting from current position in new order
                    let newContinuous = [];
                    for (let j = i; j < this.thumbnailContainerList[containerIndex].thumbnailList.length; j++) {
                        let nextThumbnail = this.thumbnailContainerList[containerIndex].thumbnailList[j];
                        let nextFunction = nextThumbnail.getFunctionForSelection();
                        if (nextFunction && nextFunction.continuous && nextFunction.continuous[0]) {
                            newContinuous.push(nextFunction.continuous[0]);
                        }
                    }

                    functionForSelection.continuous = newContinuous;
                    thumbnail.setFunctionForSelection(functionForSelection);
                }
            }

            // STEP 6: Scroll container to ensure focused thumbnail remains visible
            // If the focused thumbnail moved outside the viewport, scroll to show it
            this.scrollThumbnails();

        }
    }

    /**
     * Remove the given container block from the DOM and from the menuDict as well
     *
     * AmazonQ generated this code - the deletion from the DOM
     *
     * @param {*} domThumbnailContainerBlock
     */
    clickedOnDeleteThumbnailContainer(thumbnailContainer, domThumbnailContainerBlock) {
        let request = thumbnailContainer.request;
        let containerId = domThumbnailContainerBlock.attr('id');
        let containerIndex = parseInt(containerId.replace('container-block-', ''));

        //
        // Remove from the menuDict
        //
        let oContainerGenerator = this.oContainerGenerator;
        let origMenuDict = oContainerGenerator.getMenuDict();
        let container_list = origMenuDict.container_list ?? [];

        // Remove the container at containerIndex from the container_list
        if (container_list && container_list.length > containerIndex) {
            container_list.splice(containerIndex, 1);

            // Update the menuDict with the modified container_list
            origMenuDict.container_list = container_list;

            // If you need to save or update the menuDict elsewhere, do it here
            // For example: oContainerGenerator.setMenuDict(origMenuDict);
        }

        //
        // Remove from DOM
        //
        domThumbnailContainerBlock.remove();

        // Remove from internal data structures
        this.thumbnailContainerList.splice(containerIndex, 1);
        this.focusedThumbnailList.splice(containerIndex, 1);
        this.numberOfContainers--;

        // Update the IDs of all subsequent container blocks to maintain sequential numbering
        for (let i = containerIndex; i < this.numberOfContainers; i++) {
            let nextBlock = $('#container-block-' + (i + 1));
            nextBlock.attr('id', 'container-block-' + i);

            // Update the container space ID as well
            let nextSpace = $('#container-space-' + (i + 1));
            nextSpace.attr('id', 'container-space-' + i);

            // Update the container ID
            let nextContainer = $('#container-' + (i + 1));
            nextContainer.attr('id', 'container-' + i);

            // Update the thumbnails within this container
            nextContainer.children('.thumbnail').each(function() {
                let thumbnailElement = $(this);
                let id = thumbnailElement.attr('id');
                // Replace the container index part of the ID
                thumbnailElement.attr('id', id.replace(/-(\d+)-/, '-' + i + '-'));
            });

            // Update the container's reference to its index
            if (this.thumbnailContainerList[i]) {
                this.thumbnailContainerList[i].setParent(this, i);
            }
        }

        // Refresh the DOM reference
        this.domThumbnailContainerBlocks = $('#scroll-section .thumbnail-container-block');

        // If we removed the currently focused container, adjust the focus
        if (this.currentContainerIndex >= this.numberOfContainers) {
            this.currentContainerIndex = Math.max(0, this.numberOfContainers - 1);
        }

        // Update the focus if there are still containers
        if (this.numberOfContainers > 0) {
            this.focus();
        } else {
            // Clear the description section if all containers are removed
            // this.oDescriptionContainer.clearDescription();
        }
    }

    /**
     * Edit the given container block in the DOM and in the menuDict as well
     *
     * AmazonQ generated this code - the deletion from the DOM
     *
     * @param {*} domThumbnailContainerBlock
     */
    clickedOnEditThumbnailContainer(thumbnailContainer, domThumbnailContainerBlock) {
        let request = thumbnailContainer.request;
        let containerId = domThumbnailContainerBlock.attr('id');
        let containerIndex = parseInt(containerId.replace('container-block-', ''));

        //
        // Fetch the container_list what we modify
        //

        let data_dict = request.rq_data;
        let show_level = request.rq_path;
        let container_title = request.title;

//        let oContainerGenerator = this.oContainerGenerator;
//        let origMenuDict = oContainerGenerator.getMenuDict();
//        let container_list = origMenuDict.container_list ?? [];
//
//        let data_dict = container_list[containerIndex]['dynamic_hard_coded']['data'];
//        let show_level = container_list[containerIndex]['dynamic_hard_coded']['request']['path'];


//        // TODO:
//        let container_title = container_list[containerIndex]['dynamic_hard_coded']['title'][0]['text'];

        data_dict["show_level"] = show_level;
        data_dict["container_title"] = container_title;

        this.objThumbnailController.editThumbnailContainerForm(data_dict, containerIndex);
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


    /**
     * Gets the index of the currently focused thumbnail in the current container
     * @returns {number} The index of the focused thumbnail (0-based)
     */
    getFocusedThumbnailIndex() {
        return this.focusedThumbnailList[this.currentContainerIndex];
    }

    /**
     * Moves focus to the thumbnail at the specified index in the current container
     * @param {number} thumbnailIndex - The index of the thumbnail to focus on (0-based)
     */
    setFocusToThumbnail(thumbnailIndex) {
        if (!this.focusedThumbnailList || !this.focusedThumbnailList.length) {
            return;
        }

        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
        if (thumbnailIndex < 0 || thumbnailIndex >= domThumbnails.length) {
            return; // Invalid index
        }

        let currentThumbnailIndex = this.focusedThumbnailList[this.currentContainerIndex];

        // Hide current focus
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');

        // Show new focus
        domThumbnails.eq(thumbnailIndex).css('border-color', thumbnail_border_color);
        this.focusedThumbnailList[this.currentContainerIndex] = thumbnailIndex;
        this.scrollThumbnails();
        this.showDetails();
    }


    /**
     * Calculates the indices of the first and last thumbnails that are fully visible in the current container's viewport.
     *
     * This method determines which thumbnails are completely within the visible scrollable area of the container,
     * excluding any partially visible thumbnails at the edges. Uses Math.round() to handle floating-point precision
     * issues that can occur with CSS pixel calculations.
     *
     * AmazonQ generated this viewport calculation logic and floating-point precision fix
     *
     * @returns {Array<number>} A two-element array [firstIndex, lastIndex] where:
     *   - firstIndex: The index of the first fully visible thumbnail (0-based)
     *   - lastIndex: The index of the last fully visible thumbnail (0-based)
     *   - Returns [0, 0] if no thumbnails exist in the container
     *
     * @example
     * // With 9 thumbnails where indices 4-8 are fully visible:
     * const [first, last] = getIndexOfFirstAndLastThumbnailInViewPort();
     * // Returns [4, 8]
     */
    getIndexOfFirstAndLastThumbnailInViewPort() {
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
        if (domThumbnails.length === 0) return [0, 0];

        let domContainer = $('#container-' + this.currentContainerIndex);
        let containerScrollLeft = Math.round(domContainer.scrollLeft());
        let containerWidth = Math.round(domContainer.width());
        let viewportRight = containerScrollLeft + containerWidth;

        let firstFullyVisibleIndex = -1;
        let lastFullyVisibleIndex = -1;

        domThumbnails.each(function(index) {
            let thumbnail = $(this);
            let thumbnailLeft = Math.round(thumbnail.position().left + containerScrollLeft);
            let thumbnailRight = thumbnailLeft + Math.round(thumbnail.outerWidth());

            // Check if thumbnail is FULLY visible in viewport
            if (thumbnailLeft >= containerScrollLeft && thumbnailRight <= viewportRight) {
                if (firstFullyVisibleIndex === -1) firstFullyVisibleIndex = index;
                lastFullyVisibleIndex = index;
            }
        });

        return [firstFullyVisibleIndex === -1 ? 0 : firstFullyVisibleIndex, lastFullyVisibleIndex === -1 ? 0 : lastFullyVisibleIndex];
    }






    // Take the next thumbnail
    arrowRight() {
        if (!this.focusedThumbnailList || !this.focusedThumbnailList.length) {
            return;
        }

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
        if (!this.focusedThumbnailList || !this.focusedThumbnailList.length) {
            return;
        }

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
        if (!this.focusedThumbnailList || !this.focusedThumbnailList.length) {
            return;
        }

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
        if (!this.focusedThumbnailList || !this.focusedThumbnailList.length) {
            return;
        }

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

        if (this.focusedThumbnailList && this.focusedThumbnailList.length > 0) {
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
//    constructor(title, defaultThumbnailIndex = 0) {
    constructor(request, title, defaultThumbnailIndex = 0) {
        this.request = request;
        this.title = title;
        this.numberOfThumbnails = undefined;
        this.defaultThumbnailIndex = defaultThumbnailIndex;
        this.currentThumbnailIndex = undefined;
        this.thumbnailList = [];

        // this part is newly added
        this.index = null;
        this.objScrollSection = null;

        this.resetDom();
    }

    setParent(objScrollSection, index) {
        this.index = index;
        this.objScrollSection = objScrollSection;
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
//    addThumbnail(recordId, objThumbnail) {
    addThumbnail(objThumbnail) {
            let refToThis = this;
        let thumbnailIndex = this.thumbnailList.length;
        this.thumbnailList.push(objThumbnail);

        this.coreDomeBuild(thumbnailIndex, objThumbnail);

        // If the ObjThumbnailContainer was already added to the ObjScrollSection, then the click listener should be configured
        if(this.objScrollSection !== null && this.objScrollSection !== undefined && this.index != null){
            let domThumbnail = $(`div.thumbnail#container-${this.index}-thumbnail-${thumbnailIndex}`)
            domThumbnail.click(function () {
                refToThis.objScrollSection.clickedOnThumbnail($(this).attr('id'));
            });
        }
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

            // if it has index => the container was already added to the ScrollSection
            id: "container-" + (this.index ?? "{???}") + "-thumbnail-" + thumbnailIndex });
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
        if(level && ( level == "series" || level =="remake" || level == "sequel" || level == "season" || level == "episode" || level == "lp" || level == "band" || level == "soundtrack" || level == "record")){
            let ribbonText = get_translated_level(level);

            // Add sequence number for season and episode levels
            if(((level == "season" || level == "episode") || (level == "lp" || level == "record"))  && extras["sequence"] && extras["sequence"] >= 0){
                ribbonText += ": " + extras["sequence"];
            }

            let domLevelRib = $("<div>",{
                class: "ribbon-level",
                level: level,
                text: ribbonText
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

    setExtras({ medium_path = undefined, download = undefined, length = undefined, full_time = undefined, net_start_time = undefined, net_stop_time = undefined, date = undefined, origins = undefined, genres = undefined, themes = undefined, level = undefined, recent_state = {}, rate = undefined, skip_continuous_play = undefined, tags = [], sequence = undefined}) {
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

        this.thumbnailDict["extras"]["sequence"] = sequence;
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

    getThumbnailController(){
        return this.objThumbnailController;
    }




    handleTagDelete(event, card_id, tag_name, hash, mainObject) {
        event.stopPropagation(); // Prevent event bubbling

        // Remove the tag from the DB
        const rq_method = "DELETE";
        const rq_url = "http://" + host + port + "/personal/tag/delete";
        const rq_data = {"card_id": card_id, "name": tag_name};

        const response = $.getJSON({
            method: rq_method,
            url: rq_url,
            async: false,
            dataType: "json",
            data: rq_data
        });

        // If the removal was successful
        if(response.status == 200){
            // Remove the tag from the screen
            $('#description-tagging-' + hash).remove();

            // Remove the tag from the hierarchy for ALL Thumbnails in all ThumbnailContainer
            mainObject.objScrollSection.thumbnailContainerList.forEach(objThumbnailContainer => {
                objThumbnailContainer.thumbnailList.forEach(thumbnail => {
                    const single = thumbnail.function_for_selection.single;
                    if("medium_dict" in single){
                        const other_card_id = single.medium_dict["card_id"];
                        if(other_card_id == card_id){
                            thumbnail.removeExtrasTag(tag_name);
                        }
                    }
                });
            });

            // Get the new list of tags
            const data = {
                "category": "movie",
                "limit": 9999,
            };
            all_movie_tag_dict = getAllElements("list_to_dict", data, "/collect/tags");
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
                let descTaggingDiv = $("#description-tagging");
                descTaggingDiv.empty();

                if(extra["medium_path"]){

                    // Construct + button
                    let tagButton = $('<div>', {
                        id: 'description-tagging-add',
                        class: "description-tagging-button"
                    });
                    let tagButtonAdd = $('<span>', {
                        class: "description-tagging-button-add",
                        //➕
                        text: "  \u{2795}  "
                    });
                    tagButton.append(tagButtonAdd);
                    descTaggingDiv.append(tagButton);

                    $("#description-tagging")

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
                        descTaggingDiv.append(tagButton);

                        tagButtonClose.on("click", (event) => {mainObject.handleTagDelete(event, card_id, tag_name, hash, mainObject);});
                    }

                    // 'Add TAG' listener
                    tagButtonAdd.on("click", function() {

                        // Disable the global key event listener
                        let orig_focus_task = refToObjThumbnailController.focusTask
                        refToObjThumbnailController.focusTask = FocusTask.Text;

                        tagButton.hide(); // Hide the + button

                        // Create text field
                        let textField = $('<input>', {
                            type: 'text',
                            class: 'description-tagging-field',
                            id: 'description-tagging-field',
                        });

                        // put the text field in the first position
                        descTaggingDiv.prepend(textField); // Add text field
                        //createFreeComboBoxWithDict('description-tagging-field', all_movie_tag_dict);

                        createFreeComboBoxWithDict('description-tagging-field', all_movie_tag_dict)

                        $('#description-tagging').css({
                            'display': 'flex',
                            'align-items': 'center'
                        });
                        $('.custom-combobox-description-tagging-field').css({
                            'font-family': 'inherit',
                            'font-size': '16px',
                            'margin': '0 0 0 0',
                          });
                        // Now manually style the elements
                        $('#description-tagging-field').css({
                            'font-family': 'inherit',
                            'font-size': '16px',
                            'font-weight': 'bold',
                            'outline': 'none',
                            'border-color': '#4CAF50',
                            'border-width': '3px',
                            'margin': '0 0 0 0',
                          });
                        $('.combobox-toggle-description-tagging-field').css({
                            'height': '30px',
                            'margin': '0 0 0 0',
                            'padding': '0 4px',
                            'border-top-left-radius': '0',
                            'border-bottom-left-radius': '0',
                            'border-top-right-radius': '5px',     /* Added right side rounding */
                            'border-bottom-right-radius': '5px',  /* Added right side rounding */
                            'border-left': 'none'
                          });

                        textField = $('#description-tagging-field')

                        // Focus on the text field
                        textField.focus();

                        // Event for when the text field loses focus
                        textField.on('blur', function() {
                            textField.remove();     // Remove text field
                            tagButton.show();       // Show the + button again

                            $('.custom-combobox-description-tagging-field').remove();

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
                                        descTaggingDiv.append(tagButton);

                                        tagButtonClose.on("click", (event) => {mainObject.handleTagDelete(event, card_id, tag_name, hash, mainObject);});

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

                                        // Get the new list of tags
                                        data = {
                                            "category": "movie",
                                            "limit": 9999,
                                        };
                                        all_movie_tag_dict = getAllElements("list_to_dict", data, "/collect/tags");
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

                mainObject.printCredentals(credTable, credentials, "performers", translated_labels.get('performer') + ":");
                mainObject.printCredentals(credTable, credentials, "directors", translated_labels.get('director') + ":");
                mainObject.printCredentals(credTable, credentials, "writers", translated_labels.get('writer') + ":");
                mainObject.printCredentals(credTable, credentials, "stars", translated_labels.get('star') + ":");
                mainObject.printCredentals(credTable, credentials, "actors", translated_labels.get('actor') + ":");
                mainObject.printCredentals(credTable, credentials, "voices", translated_labels.get('voice') + ":");
                mainObject.printCredentals(credTable, credentials, "hosts", translated_labels.get('host') + ":");
                mainObject.printCredentals(credTable, credentials, "guests", translated_labels.get('guest') + ":");
                mainObject.printCredentals(credTable, credentials, "interviewers", translated_labels.get('interviewer') + ":");
                mainObject.printCredentals(credTable, credentials, "interviewees", translated_labels.get('interviewee') + ":");
                mainObject.printCredentals(credTable, credentials, "presenters", translated_labels.get('presenter') + ":");
                mainObject.printCredentals(credTable, credentials, "lecturers", translated_labels.get('lecturer') + ":");
                mainObject.printCredentals(credTable, credentials, "reporters", translated_labels.get('reporter') + ":");

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

        let domDescriptionTextContainerOuter = $("#description-text-container-outer");
        let textContainerOuterBorderHeight = domDescriptionTextContainerOuter.outerHeight()- domDescriptionTextContainerOuter.innerHeight();

        let domDescriptionTextContainer = $("#description-text-container");
        let textContainerBorderHeight = domDescriptionTextContainer.outerHeight()- domDescriptionTextContainer.innerHeight();

        let domDescriptionTextExtra = $("#description-text-extra");
        let extraHeight = domDescriptionTextExtra.outerHeight();
        let domDescriptionTextArea = $("#description-text-area-div");
        let areaBorderHeight = domDescriptionTextArea.outerHeight() - domDescriptionTextArea.innerHeight()
        let storylineHeight = textWrapperHeight - titleHeight - textContainerOuterBorderHeight - textContainerBorderHeight - extraHeight - appendixHeight - areaBorderHeight;
        let credentialHeight = textWrapperHeight - titleHeight -  textContainerOuterBorderHeight - appendixHeight;

        t.style.setProperty('--description-text-storyline-height', storylineHeight + 'px');
        t.style.setProperty('--description-text-credentials-height', credentialHeight + 'px');
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

                if(typeof item === 'object'){
                    const [key, value] = Object.entries(item)[0];
                    const joinedString = value.join(', ')
                    column = $("<td>");
                    column.text(key + ":");
                    line.append(column);
                    column = $("<td>");
                    column.text(joinedString);
                    line.append(column);

                }else{
                    column = $("<td>");
                    column.text(item);
                    line.append(column);
                }

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

        link = this.levelList.length ? "" + this.levelList[this.levelList.length - 1]["text"] : "";
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
    static Modal_Login = new FocusTask('modal_login');
    constructor(name) {
        this.name = name
    }
}


var search_merge_something;

/**
 * Global function to handle search filter form data for both adding and modifying containers
 *
 * @param {Object|null} data_dict - Dictionary with filter values (null for new container, populated for modification)
 * @param {Object} callbacks - Object containing callback functions
 * @returns {Object} - Dialog configuration object
 */
function searchFilterForm(callbacks = {}, menu_dict, data_dict = null) {

    // Initialize empty data if not provided (for adding new container)
    if (data_dict === null) {

        data_dict = {
            "container_title": ""
        }
        menu_dict["used_fields"].forEach(field => {
            data_dict[field["dict_id"]] = field["default"];
        });
    }
//        data_dict = {
//            "container_title": "",
//            "genres": "",
//            "themes": "",
//            "directors": "",
//            "writers": "",
//            "actors": "",
//            "voices": "",
//            "origins": "",
//            "tags": "",
//            "show_level": "/collect/highest/mixed",
//            "view_state": "",
//            "rate": ""
//        };
//    }

    let dialog_dict = translated_interaction_labels.get('dialog');
    let submit_button = dialog_dict['search']['buttons']['submit'];
    let cancel_button = dialog_dict['search']['buttons']['cancel'];

    /* Search dialog form */
    $("#dialog-form-search label[for='dialog-search-container-title']").html(dialog_dict['search']['labels']['container_title'] + ': ');
    $("#dialog-search-container-title").val(data_dict["container_title"] || "");

    // Hide all search fields by default (except title and separator)
    $("#dialog-form-search table tr").not(":first, :has(.dialog-search-separator)").hide();

    //
    // Show only fields specified in used_fields
    //
    if (menu_dict && menu_dict["used_fields"]) {
        menu_dict["used_fields"].forEach(field => {
            $("#" + field["tr_id"]).show();

            // Show translated label
            $("#dialog-form-search label[for='" + field["label_for"] + "']").html(dialog_dict['search']['labels'][field['translate_dialog_label']] + ': ');

        });
    }

    // list for variables for the fields
    let search_var_dict = {};

    // Default submit callback if not provided
    const submitCallback = callbacks.onSubmit || function(formData) {
        console.log("Form submitted with data:", formData);
    };

    // Default cancel callback if not provided
    const cancelCallback = callbacks.onCancel || function() {
        console.log("Form cancelled");
    };

    // Default beforeClose callback if not provided
    const beforeCloseCallback = callbacks.beforeClose || function(event, refToThis) {
        if (event.originalEvent && event.originalEvent.key === "Escape") {
            // Delay needed to not propagate ESC
            setTimeout(function () {
                refToThis.focusTask = refToThis.originalTask;
            }, 200);
        } else {
            refToThis.focusTask = refToThis.originalTask;
        }
    };

    // Return the dialog configuration
    return {
        title: dialog_dict['search']['title'],
        submit_button: submit_button,
        cancel_button: cancel_button,

        // Dialog configuration
        dialogOptions: function(refToThis) {
            return {
                resizable: false,
                height: "auto",
                width: 1000,
                modal: true,
                title: dialog_dict['search']['title'],
                buttons: {
                    [submit_button]: function() {
                        $(this).dialog("close");

                        //
                        // Collect the values of fields to send it the the REST request
                        //
                        var formData = {
                            "container_title": $("#dialog-search-container-title").val()
                        };

                        // Values from the form
                        menu_dict["used_fields"].forEach(field => {
                            let inputId = field["input_id"]
                            let dictId = field["dict_id"]

                            if (field["field_type"] === "combo-box-with-dict"){
                                formData[dictId] = search_var_dict[inputId].getMergedValues();

                            }else if(field["field_type"] === "auto-complete"){
                                formData[dictId] = search_var_dict[inputId].getMergedValues();

                            }else{
                                formData[dictId] = search_var_dict[inputId].val();
                            }
                        });

                        // Static values
                        menu_dict["static_fields"].forEach( field => {
                            formData[field["field_name"]] = field["field_value"]
                        });

                        submitCallback(formData);
                    },
                    [cancel_button]: function() {
                        $(this).dialog("close");
                        cancelCallback();
                    }
                },

                // Right/Left button to focus buttons
                open: function() {

                    //
                    // Construct the fields and set them with values (new: default values / modify: existing values)
                    //
                    menu_dict["used_fields"].forEach(field => {
                        let inputId = field["input_id"]
                        let optionsDictVarName = field["options_dict_variable_name"]

                        if (field["field_type"] === "combo-box-with-dict"){
                            search_var_dict[inputId] = createComboBoxMergeWithDict(inputId, eval(optionsDictVarName));
                            search_var_dict[inputId].setItems(parseMergedDictElements(data_dict[field["dict_id"]], eval(optionsDictVarName)));
                        }else if(field["field_type"] === "auto-complete"){
                            search_var_dict[inputId] = createFieldWithAutocompleteMergeFromList(inputId, eval(optionsDictVarName));
                            search_var_dict[inputId].setItems(parseMergedListElements(data_dict[field["dict_id"]]));
                        }else{
                            // First fill up the dropdown (possible) values
                            search_var_dict[inputId] = $("#" + inputId);
                            Object.entries(eval(optionsDictVarName)).forEach(([key, value]) => {
                                $("#dialog-form-search select option[value='" + key + "']").html(value);
                            });
                            search_var_dict[inputId].val(data_dict[field["dict_id"]]);
                        }
                    });

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

                    // Calculate and set the horizontal divider
                    $('.dialog-search-separator').css('width', `calc(100% + 24px)`);
                },

                // Prevent the ESC button to go back in history
                beforeClose: function(event) {
                    beforeCloseCallback(event, refToThis);
                },

                // It executed anyway
                close: function() {
                    $(document).off("keydown.arrowKeys");
                    $(this).dialog("destroy");
                }
            };
        }
    };
}


class ThumbnailController {

    constructor(mainMenuGenerator) {
        this.language_code = mainMenuGenerator.language_code;
        this.history = new History();
        this.focusTask = FocusTask.Menu;
        this.updateMediaHistoryIntervalId = null;
        this.media_history_start_epoch = null;

        this.objScrollSection = new ObjScrollSection({ oContainerGenerator: mainMenuGenerator, objThumbnailController: this });

        // Listener for History back
        let tshl = $("#history-section-link");
        tshl.click(function () {
            let esc = $.Event("keydown", { keyCode: 27 });
            $(document).trigger(esc);
        });

        let refToThis = this;

        // Listener for Control Container Add link
        let ccas = $("#container-controllers-add");
        ccas.click(function () {
            refToThis.addNewThumbnailContainerForm();
        });
    }


    editThumbnailContainerForm(data_dict, containerIndex) {
        let refToThis = this;

        let menu_dict = this.objScrollSection.oContainerGenerator.menu_dict

        // Disable keys behind the Dialog() - prevent the ESC button to go back in history
        refToThis.originalTask = refToThis.focusTask;
        refToThis.focusTask = FocusTask.Modal_Continue_Play;

        // Define callbacks for the form
        const callbacks = {
            onSubmit: function(formData) {
                refToThis.updateThumbnailContainerExecution(formData, containerIndex);
            },
            onCancel: function() {
                // Nothing special needed on cancel
            },
            beforeClose: function(event, refToThis) {
                if (event.originalEvent && event.originalEvent.key === "Escape") {
                    // Delay needed to not propagate ESC
                    setTimeout(function () {
                        refToThis.focusTask = refToThis.originalTask;
                    }, 200);
                } else {
                    refToThis.focusTask = refToThis.originalTask;
                }
            }
        };

        // Use the global searchFilterForm function to set up the form and get dialog options
        const dialogConfig = searchFilterForm( callbacks, menu_dict, data_dict);

        // Wait 200ms before showing the Dialog
        setTimeout(() => {
            $("#dialog-form-search").dialog(dialogConfig.dialogOptions(refToThis));
        }, 200);
    }


    addNewThumbnailContainerForm(){
        let refToThis = this;

        let menu_dict = this.objScrollSection.oContainerGenerator.menu_dict

        // Disable keys behind the Dialog() - prevent the ESC button to go back in history
        refToThis.originalTask = refToThis.focusTask;
        refToThis.focusTask = FocusTask.Modal_Continue_Play;

//        let dialog_dict = translated_interaction_labels.get('dialog');
//
//        let submit_button = dialog_dict['search']['buttons']['submit'];
//        let cancel_button = dialog_dict['search']['buttons']['cancel'];

        // Define callbacks for the form
        const callbacks = {
            onSubmit: function(formData) {
                refToThis.addNewThumbnailContainerExecution(formData);
            },
            onCancel: function() {
                // Nothing special needed on cancel
            },
            beforeClose: function(event, refToThis) {
                if (event.originalEvent && event.originalEvent.key === "Escape") {
                    // Delay needed to not propagate ESC
                    setTimeout(function () {
                        refToThis.focusTask = refToThis.originalTask;
                    }, 200);
                } else {
                    refToThis.focusTask = refToThis.originalTask;
                }
            }
        };

        // Use the global searchFilterForm function to set up the form and get dialog options
        const dialogConfig = searchFilterForm(callbacks, menu_dict, null);

        // Wait 200ms before showing the Dialog
        setTimeout(() => {
            $("#dialog-form-search").dialog(dialogConfig.dialogOptions(refToThis));
        }, 200);
    }

    addNewThumbnailContainerExecution( data_dict ){
        let data = {};
        let container_title = "";
        let show_level = "";

        Object.entries(data_dict).forEach(([key, value]) => {
            if(key == "container_title"){
                container_title = value;
            }else if(key == "show_level"){
                show_level = value;
            }else if (value != "") {
                data[key] = value;
            }
        });

        if(container_title == ""){
            // TODO: must translate
            container_title = "My search"
        }

        let thumbnailContainerElement =
        {
            "dynamic_hard_coded":{
              "title": [
                  {
                      "text": container_title
                  }
              ],
              "data": data,
              "request": {
                  "method": "GET",
                  "protocol": "http",
                  "path": show_level,
                  "static": true
              }
            }
        }

        // fetch the container_list where we insert the new thumbnail container
        let oContainerGenerator = this.objScrollSection.oContainerGenerator;
        let origMenuDict = oContainerGenerator.getMenuDict();
        let container_list = origMenuDict.container_list ?? []

        // menuDict modification
        container_list.push(thumbnailContainerElement)
        origMenuDict.container_list = container_list;
        oContainerGenerator.setMenuDict(origMenuDict);

        // Scroll Section added
        this.objScrollSection = this.generateScrollSection(oContainerGenerator, self.history);
    }


    updateThumbnailContainerExecution(data_dict, containerIndex){
        let data = {};
        let container_title = "";
        let show_level = "";

        Object.entries(data_dict).forEach(([key, value]) => {
            if(key == "container_title"){
                container_title = value;
            }else if(key == "show_level"){
                show_level = value;
            }else if (value != "") {
                data[key] = value;
            }
        });

        if(container_title == ""){
            // TODO: must translate
            container_title = "My search"
        }

        let thumbnailContainerElement =
        {
          "dynamic_hard_coded":{
              "title": [
                  {
                      "text": container_title
                  }
              ],
              "data": data,
              "request": {
                  "method": "GET",
                  "protocol": "http",
                  "path": show_level,
                  "static": true
              }
          }
        }

        // fetch the container_list where we insert the new thumbnail container
        let oContainerGenerator = this.objScrollSection.oContainerGenerator;
        let origMenuDict = oContainerGenerator.getMenuDict();
        let container_list = origMenuDict.container_list ?? []

        container_list[containerIndex] = thumbnailContainerElement
        origMenuDict.container_list = container_list;
        oContainerGenerator.setMenuDict(origMenuDict);

        // Scroll Section added
        this.objScrollSection = this.generateScrollSection(oContainerGenerator, self.history);
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

        if(hit["is_appendix"] !== true){
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


    playMediaAudioVideo(continuous_list){

        // Takes the first element from the list
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

                // Disable keys behind the Dialog()
                refToThis.originalTask = refToThis.focusTask;
                refToThis.focusTask = FocusTask.Modal_Continue_Play;

                let continue_button = translated_interaction_labels.get('dialog')['continue_interrupted_playback']['buttons']['continue'];
                let from_beginning_button = translated_interaction_labels.get('dialog')['continue_interrupted_playback']['buttons']['from_beginning']

                // Wait 200ms before I show the Dialog(), otherwise, the Enter, which triggered this method, would click on the first button on the Dialog(), close the Dialog and start the play
                setTimeout(() => {
                    $("#dialog-confirm-continue-interrupted-play p").html(translated_interaction_labels.get('dialog')['continue_interrupted_playback']['message']);
                    $("#dialog-confirm-continue-interrupted-play").dialog({

                        //closeOnEscape: false,
                        resizable: false,
                        height: "auto",
                        width: 400,
                        modal: true,
                        zIndex: 1100,
                        title: translated_interaction_labels.get('dialog')['continue_interrupted_playback']['title'],

                        buttons: {
                            [continue_button]: function() {
                                $( this ).dialog( "close" );
                                refToThis.configurePlayer(refToThis, continuous_list, recent_position);
                            },
                            [from_beginning_button]: function() {
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

                        beforeClose: function(event){

                            if (event.originalEvent && event.originalEvent.key === "Escape") {

                                // Delay needed to not propagate ESC
                                setTimeout(function () {
                                    refToThis.focusTask = refToThis.originalTask;
                                }, 200);
                            }else{
                                refToThis.focusTask = refToThis.originalTask;
                            }
                        },

                        close: function() {
                            $(document).off("keydown.arrowKeys"); // Remove listener on close
                            $(this).dialog("destroy");
                        }
                    });
                }, 200);

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

        // Preserve aspect ratio of poster/screenshot images
        player.style.objectFit = 'contain';
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

        refToThis.focusTask = FocusTask.Player;
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
        this.playMediaCode(medium_dict);
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
//                player.play();

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
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else if (document.webkitFullscreenElement) {
                document.webkitExitFullscreen();
            } else if (document.mozFullScreenElement) {
                document.mozCancelFullScreen();
            }
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
        } else if (this.focusTask === FocusTask.Player) {
            let player = $("#video_player")[0];
            player.currentTime = Math.max(0, player.currentTime - 10);
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

        } else if (this.focusTask === FocusTask.Player) {
            let player = $("#video_player")[0];
            player.currentTime = Math.min(player.duration, player.currentTime + 10);

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
        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data });

        let response_dict = response.responseJSON;
        let result = response_dict['result'];
        let data_list = response_dict['data'];

        // If the query was OK and there was 1 record
        if (result && data_list.length > 0){
            let result_dict = data_list[0];
            return result_dict['recent_position'];
        }else{
            return 0;
        }
    }
}

