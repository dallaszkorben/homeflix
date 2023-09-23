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
    constructor(numberOfContainers, defaultContainerIndex=0){
        this.numberOfContainers = numberOfContainers
        this.defaultContainerIndex = defaultContainerIndex;
        this.currentContainerIndex = -1;
        this.thumbnailIndexList = [];
//        this.thumbnailContainerList = [];

        // Remove all elements from the <div id=thumbnail-sections> and <div id=detail-text-title> and <div id=detail-image-div>
        this.thumbnailSection = $("#thumbnail-section");
        this.thumbnailSection.empty();
        
        let domThumbnailSectionHistory = $("<div>",{
            id: "thumbnail-section-history",
            text: "> "
        });

        this.thumbnailSection.append(domThumbnailSectionHistory);
     
    }

    addThumbnailContainerObject(title, thumbnailContainer){
//        let containerIndex = this.thumbnailContainerList.length;
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
        this.thumbnailSection.append(domThumbnailContainerBlock);
        
//        this.thumbnailContainerList.push(thumbnailContainer);
    }

    selectDefault(){
        this.currentContainerIndex = 0;
        let domThumbnails = $('#container-' + this.currentContainerIndex + ' .thumbnail');
//        thumbnailContainerBlocks = $('#section .thumbnail-container-block');

        let currentThumbnailIndex = this.thumbnailIndexList[this.currentContainerIndex];
        domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
    }
    
}
//         selectDefaultThumbnail(){
//             var containers = this.sectionsMap["sections"][this.sectionIndex]["containers"];
//             var defaultContainer = containers[defaultCurrentContainerIndex]
//             if(this.containerIndex==defaultCurrentContainerIndex && defaultContainer !== undefined){

//                 var defaultThumbnailContainerId = this.sectionsMap["sections"][this.sectionIndex]["containers"][defaultCurrentContainerIndex]["container-id"];           
//                 var thumbnailClass = this.attributeMap["thumbnail-class"];
//                 var defaultThumbnails = $("#" + defaultThumbnailContainerId + " ." + thumbnailClass);
//                 var defaultThumbnail = defaultThumbnails.eq(defaultCurrentThumbnailIndex);

//                 // Turn off listeners

//                 selectThumbnail(defaultThumbnail);                                

//                 // Turn back listeners
//             }
//         }

//         collectDataAndShowContainer(){
//             throw new Error('You have to implement the method collectDataAndShowContainer()!');
//         }

//         /*
//         This method should be called if all data was collected to be able to show the container
//         The boxess is a list of box
//         The box is a dictionary with:
//         "text", 
//         "image", 
//         "fn_focus", 
//         "fn_select"
//         */
//         show(boxes){

//             // Add empty container to the container list and create and return thumbnail-container object

//             var sectionId = sectionsMap["sections"][this.sectionIndex]["section-id"]
//             var containerId = sectionsMap["sections"][this.sectionIndex]["containers"][this.containerIndex]["container-id"];
//             var thumbnailContainer = $("#" + containerId);
            
//             // Show container title
//             $("#"+containerId).prev(".thumbnail-container-title").text(this.title);

//             for(var thumbnailIndex=0; thumbnailIndex<boxes.length; thumbnailIndex++){

//                 // -----------
//                 // DOM
//                 // -----------

//                 // Create thumbnail
//                 var thumbnail = $("<div>", {
//                     class: attributeMap["thumbnail-class"],
//                     id: attributeMap["thumbnail-id"].format(this.sectionIndex, this.containerIndex, thumbnailIndex)
//                 });

//                 // Add Text to image
//                 var textWrapper = $("<div>", {
//                     class: attributeMap["thumbnail-text-wrapper-class"],
//                 });
//                 thumbnail.append(textWrapper);  

//                 var text = $("<div>", {
//                     class: attributeMap["thumbnail-text-class"],
//                     text: boxes[thumbnailIndex].getText(),
//                 });
//                 textWrapper.append(text);  

//                 // Create image
//                 var image = $("<img>",{
//                     src: boxes[thumbnailIndex].getImage(),
//                     alt: "Image",
//                 });
//                 thumbnail.append(image);                 

//                 // CLICK/SELECT event for thumbnail
//                 // This special mechanism needed, otherwise the Function On Select always on the LATEST boxes[box] would be executed
//                 // thumbnail.click(function(){
//                 //     boxes[box].getFunctionOnSelect()();
//                 // });
//                 thumbnail.click((function(actualBox){
//                     return function(event){
//                         selectThumbnail($(event.currentTarget));
//                         actualBox.getFunctionOnSelect()();
//                     }
//                 })(boxes[thumbnailIndex]));

//                 //FOCUS event for thumbnail
//                 // This special mechanism needed, otherwise the Function On Container Focus always on the LATEST boxes[box] would be executed
//                 // thumbnail.on("containerFocusEvent", function(event) {
//                 //     boxes[box].getFunctionOnFocus()();
//                 // });
//                 thumbnail.on("containerFocusEvent", (function(actualBox){
//                     return function(event){
//                         actualBox.getFunctionOnFocus()();
//                     }
//                 })(boxes[thumbnailIndex]));


// //!!!

//                 // Place thumbnail into thumbnail-container
//                 thumbnailContainer.append(thumbnail);

//                 // -----------
//                 // sectionsMap
//                 // -----------
 
//                 // Add an empty thumbnail to the thumbnail list

//                 var newLength = sectionsMap["sections"][this.sectionIndex]["containers"][this.containerIndex]['thumbnails'].push({});
//                 sectionsMap["sections"][this.sectionIndex]["containers"][this.containerIndex]["thumbnails"][thumbnailIndex]["thumbnail-id"] = thumbnail.attr('id');

//             }               
            
// //TODO:!!!! this.section.append(title);

//             // selection border for the default first thumbnail - it is possible as at least one section container is done
//             this.selectDefaultThumbnail();   
            
// //            $("#section-0_container-0").focus();
//         }   
    

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

    /**
     * 
     * <div class="thumbnail" id="container-1_thumbnail-0">
     *   <div class="thumbnail-text-wrapper">
     *     <div class="thumbnail-text">1. box</div>
     *   </div>
     *   <img src="images/categories/movie.jpg" alt="Image">
     * </div>
     *
     * @param {*} recordId 
     * @param {*} thumbnailSrc 
     * @param {*} descriptionSrc 
     * @param {*} title 
     * @param {*} titleOrig 
     * @param {*} langOrig 
     */
    addThumbnail(recordId, thumbnailSrc, descriptionSrc, thumbTitle, title, titleOrig, langOrig){
        let thumbnailDict = {
            "record_id": recordId,
            "thumbnail_src": thumbnailSrc,
            "description_src": descriptionSrc,
            "thumb_title": thumbTitle,
            "title": title,
            "title_orig": titleOrig,
            "lang_orig": langOrig
        };
        let thumbnailIndex = this.thumbnailList.length;
        this.thumbnailList.push(thumbnailDict);
        let domThumbnail = $("<div>",{
            class: "thumbnail",
            id: "container-{???}-thumbnail-" + thumbnailIndex
        });
        let domThumbnailTextWrapper = $("<div>",{
            class: "thumbnail-text-wrapper",
        });
        let domThumbnailText = $("<div>",{
            class: "thumbnail-text",
            text: thumbTitle
        });
        let domImg = $("<img>",{
            src: thumbnailSrc,
            alt: "Image"
        });
        domThumbnailTextWrapper.append(domThumbnailText);
        domThumbnail.append(domThumbnailTextWrapper);
        domThumbnail.append(domImg);
        this.domThumbnailContainer.append(domThumbnail);

        // if(title){
        //     $('#detail-text-title').text(title);
        // }else{
        //     $('#detail-text-title').text(title_orig);            
        // }
    }
}


