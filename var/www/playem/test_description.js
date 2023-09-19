/**
 * The description image size will be automatically calculated when the refreshDescription() is called
 * It happens when you want to show a new description.
 * 
 */
let description_img={
    width: 0,
    height: 0
}

function printCredentals(table, dict, id, title){
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

/**
 * It resizes the description image and the description text wrapper (in the CSS) according to the available place
 * It is called when the size of the description section changed
 * Typically used by the ResizeObserver
 * 
 * @param {root from css, containing css variables} root 
 */
function resizeDescriptionSection(root){

    let descriptionTextWrapper = $("#description-text-wrapper");

    let descriptionSectionDiv = $("#description-section");
    let sectionHeight = descriptionSectionDiv.height();

    let wrapperHeight = descriptionSectionDiv.innerHeight();
    let wrapperWidth = descriptionSectionDiv.innerWidth();

    let newDescImgWidth = sectionHeight * description_img.width / description_img.height;

    // Set the width of the image accordingto its aspect ration and the available height
    root.style.setProperty('--description-image-width', newDescImgWidth + 'px');

    // Set the size of the text-wrapper div to cover the whole available space
    root.style.setProperty('--description-text-wrapper-height', wrapperHeight + 'px');
    root.style.setProperty('--description-text-wrapper-width', wrapperWidth + 'px');

    let descTextStoryline = $("#description-text-storyline");
    
    let posStoryline = descTextStoryline.position().top;
    let storylineWidth = wrapperHeight - posStoryline - 2;
    root.style.setProperty('--description-text-storyline-height', storylineWidth + 'px');
    root.style.setProperty('--description-text-credentials-height', storylineWidth + 'px');  
}

/**
 * Refreshes the Description
 * It configures an onload listener on the new image.
 * When the image loaded, this function will calculate the size of the elements in the description and
 * it will show the details
 * 
 * @param {root from css, containing css variables} root 
 * @param {*} fileName 
 * @param {*} storyline 
 * @param {*} credential 
 */
function refreshDescription(root, fileName, title, storyline, credentials, extra){
    let descImg = new Image();
    descImg.src = fileName;

    // when the image loaded, the onload event will be fired
    descImg.onload = function(){
        
        // calculates the new size of the description image
        description_img.height = descImg.height;
        description_img.width = descImg.width;
        
        // Resizes the description section according to the size of the description image
        resizeDescriptionSection(root);

        let descTextTitle = $("#description-text-title");
        descTextTitle.empty();                
        descTextTitle.html(title);


        // --- storyline ---
        let descTextStoryline = $("#description-text-storyline");
        descTextStoryline.empty();                
        descTextStoryline.html(storyline);
        // -----------------

        // --- extra ---

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

        // -------------

        // --- credentials ---
        let descTextCredentials = $("#description-text-credentials");                
        descTextCredentials.empty();

        let credTable = $("<table>",{
            border: 0,
            id: "description-text-credentials-table"
        });
        descTextCredentials.append(credTable);

        printCredentals(credTable, credentials, "directors", "Directors:");
        printCredentals(credTable, credentials, "writers", "Writers:");
        printCredentals(credTable, credentials, "stars", "Stars:");
        // -------------------
    
    }

    // Loads the new image, which will trigger the onload event
    let description_image = "url(" + descImg.src + ")";
    t.style.setProperty('--description-image', description_image);
}


