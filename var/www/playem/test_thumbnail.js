let currentContainerIndex;
let currentThumbnailIndex;
let containerNumbers;
let indexList;

let domThumbnails;
let domThumbnailContainerBlocks;

function arrowRight(){
    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
    currentThumbnailIndex = (currentThumbnailIndex + 1) % domThumbnails.length;
    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
    scrollThumbnails();
    indexList[currentContainerIndex] = currentThumbnailIndex;
}

function arrowLeft() {
    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');
    currentThumbnailIndex = (currentThumbnailIndex - 1 + domThumbnails.length) % domThumbnails.length;
    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
    scrollThumbnails();
    indexList[currentContainerIndex] = currentThumbnailIndex;
}

function arrowDown() {
    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');

    currentContainerIndex = (currentContainerIndex + 1) % containerNumbers;
    domThumbnails = $('#container-' + currentContainerIndex + ' .thumbnail');

    currentThumbnailIndex = indexList[currentContainerIndex];

    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
    scrollThumbnails();
};

function arrowUp() {
    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'transparent');

    currentContainerIndex = (currentContainerIndex - 1 + containerNumbers) % containerNumbers;
    domThumbnails = $('#container-' + currentContainerIndex + ' .thumbnail');

    // currentThumbnailIndex = 0;
    currentThumbnailIndex = indexList[currentContainerIndex];

    domThumbnails.eq(currentThumbnailIndex).css('border-color', 'red');
    scrollThumbnails();
};

function clickOnThumbnail() {
}

function scrollThumbnails() {

    // Vertical scroll                    
    var section = $('#section');
    var sectionHeight = section.height();
    var thumbnailContainerBlockHeight = domThumbnailContainerBlocks.eq(0).outerHeight(true);

    var sectionScrollTop = section.scrollTop();
    var visibleContainers = Math.floor(sectionHeight / thumbnailContainerBlockHeight);

    console.log(sectionHeight +"/" +thumbnailContainerBlockHeight + "=" + visibleContainers)

    if (currentContainerIndex >= visibleContainers + sectionScrollTop / thumbnailContainerBlockHeight) {
        section.animate({ scrollTop: thumbnailContainerBlockHeight * (currentContainerIndex - visibleContainers + 1) }, 200);
    } else if (currentContainerIndex < sectionScrollTop / thumbnailContainerBlockHeight) {
        section.animate({ scrollTop: thumbnailContainerBlockHeight * currentContainerIndex }, 200);
    }                    

    // Horizontal scroll
    var container = $('#container-' + currentContainerIndex);
    var containerWidth = container.width();
    var thumbnailWidth = domThumbnails.eq(0).outerWidth(true);

    var containerScrollLeft = container.scrollLeft();
    var visibleThumbnails = Math.floor(containerWidth / thumbnailWidth);

    if (currentThumbnailIndex >= visibleThumbnails + containerScrollLeft / thumbnailWidth) {
        container.animate({ scrollLeft: thumbnailWidth * (currentThumbnailIndex - visibleThumbnails + 1) }, 200);
    } else if (currentThumbnailIndex < containerScrollLeft / thumbnailWidth) {
        container.animate({ scrollLeft: thumbnailWidth * currentThumbnailIndex }, 200);
    }
}