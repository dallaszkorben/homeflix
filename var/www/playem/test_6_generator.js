class Generator{
    // constructor(historyDict){
    //     this.historyDict = historyDict;
    // }

    generateThumbnailSection(history={text:"", link:""}){
        let oThumbnailSection = new ObjThumbnailSection(this, history);
        oThumbnailSection.focusDefault();
        return oThumbnailSection;
    }

    sendRestRequest(rq_type, rq_url){
        let rq_assync = false;
        let result = $.getJSON({method: rq_type, url: rq_url, async: rq_assync, dataType: "json"});
        return result.responseJSON;


/*        $.ajax({ method: rq_type, url: rq_url, async: rq_assync,
            success: function(result){
                alert(result);
            },
            error: function(xhr,status,error){
                alert(status);
            }
        });

        return undefined;
*/
    }
}


class MainMenuGenerator extends Generator{

    getContainerList(){
        let refToThis = this;
        let containerList = [];

        let oContainer = new ObjThumbnailContainer("Categories");

        let thumbnail = new Thumbnail();
        let thumbnail_src, description_src,lang,original,translated,thumb,history,directors,writers,stars,length,year,origin,genre,theme
        thumbnail.setImageSources(thumbnail_src="images/categories/movie.jpg", description_src="images/categories/movie.jpg");
        thumbnail.setTitles(lang="hu", original="Movies", translated="Movies", thumb="Movies", history="Movies");
        //thumbnail.setStoryline("")
        //thumbnail.setCredentials(directors=[], writers=[], stars=[]);
        //thumbnail.setExtras(length="", year="", origin=[], genre=[], theme=[]);
        thumbnail.setGenaratorFunction({"menu": 
            (function(movie_type) {
                return function() {
                    return new MovieMenuGenerator(movie_type)
                };
            })("movies")});
        oContainer.addThumbnail(1, thumbnail);

        thumbnail = new Thumbnail();
        thumbnail.setImageSources(thumbnail_src="images/categories/series.jpg", description_src="images/categories/series.jpg");
        thumbnail.setTitles(lang="hu", original="Movie Series", translated="Movie Series", thumb="Movie Series", history="Movie Series");
        // thumbnail.setStoryline("")
        // thumbnail.setCredentials(directors=[], writers=[], stars=[]);
        // thumbnail.setExtras(length="", year=2013, origin=[], genre=[], theme=[]);
        thumbnail.setGenaratorFunction(function(){refToThis.viewMovie()});
        oContainer.addThumbnail(2, thumbnail);

        thumbnail = new Thumbnail();
        thumbnail.setImageSources(thumbnail_src="images/categories/music_video.jpg", description_src="images/categories/music_video.jpg");
        thumbnail.setTitles(lang="hu", original="Music Video", translated="Music Video", thumb="Music Video", history="Music Video");
        // thumbnail.setStoryline("")
        // thumbnail.setCredentials(directors=[], writers=[], stars=[]);
        // thumbnail.setExtras(length="", year=2013, origin=[], genre=[], theme=[]);
        thumbnail.setGenaratorFunction(function(){refToThis.viewMovie()});
        oContainer.addThumbnail(3, thumbnail);

        thumbnail = new Thumbnail();
        thumbnail.setImageSources(thumbnail_src="images/categories/music_audio.jpg", description_src="images/categories/music_audio.jpg");
        thumbnail.setTitles(lang="hu", original="Music Audio", translated="Music Audio", thumb="Music Audio", history="Music Audio");
        // thumbnail.setStoryline("")
        // thumbnail.setCredentials(directors=[], writers=[], stars=[]);
        // thumbnail.setExtras(length="", year=2013, origin=[], genre=[], theme=[]);
        thumbnail.setGenaratorFunction(function(){refToThis.viewMovie()});
        oContainer.addThumbnail(3, thumbnail);

        containerList.push(oContainer);
 
        return containerList;
    }
}


class MovieMenuGenerator extends Generator{
 
    getContainerList(){

        // TODO: must be parameterized
        let languageCode = 'en';


        let refToThis = this;
        let containerList = [];

        //
        // === Drama ===
        //
        let oContainer = new ObjThumbnailContainer("Drama");

        let requestResult = this.sendRestRequest("GET", "http://192.168.0.21/collect/standalone/movies/genre/drama/lang/" + languageCode);

        for(let line of requestResult){

            if(!line["lang_orig"]){
                line["lang_orig"] = "";
            }
            let short_title = "";
            if ( line["title_req"] != null ){
                short_title = line["title_req"];
//                line["title_orig"] = "";
            }else if ( line["title_orig"] != null ){
                short_title = line["title_orig"];
//                line["title_req"] = "";
            }
            let max_length = 20;
            if (short_title.length > max_length) {
                short_title = short_title.slice(0, max_length) + "...";
            }

            let thumbnail = new Thumbnail();
            let thumbnail_src, description_src,lang,original,translated,thumb,directors,writers,stars,length,year,origin,genre,theme
            thumbnail.setImageSources(thumbnail_src=line["source_path"]+"/thumbnail.jpg", description_src=line["source_path"]+"/movie.jpg");
            thumbnail.setTitles(lang=line["lang_orig"], original=line["title_orig"], translated=line["title_req"], thumb=short_title);
            thumbnail.setStoryline("")
            thumbnail.setCredentials(directors=[], writers=[], stars=[]);
            thumbnail.setExtras(length="", year="", origin=[], genre=[], theme=[]);
            thumbnail.setGenaratorFunction();
            oContainer.addThumbnail(1, thumbnail);
        }
        containerList.push(oContainer);

        //
        // === Drama ===
        //
        oContainer = new ObjThumbnailContainer("Comedy");

        requestResult = this.sendRestRequest("GET", "http://192.168.0.21/collect/standalone/movies/genre/comedy/lang/" + languageCode);

        for(let line of requestResult){

            if(!line["lang_orig"]){
                line["lang_orig"] = "";
            }
            let short_title = "";
            if ( line["title_req"] != null ){
                short_title = line["title_req"];
            }else if ( line["title_orig"] != null ){
                short_title = line["title_orig"];
            }
            let max_length = 20;
            if (short_title.length > max_length) {
                short_title = short_title.slice(0, max_length) + "...";
            }

            let thumbnail = new Thumbnail();
            let thumbnail_src, description_src,lang,original,translated,thumb,directors,writers,stars,length,year,origin,genre,theme
            thumbnail.setImageSources(thumbnail_src=line["source_path"]+"/thumbnail.jpg", description_src=line["source_path"]+"/movie.jpg");
            thumbnail.setTitles(lang=line["lang_orig"], original=line["title_orig"], translated=line["title_req"], thumb=short_title);
            thumbnail.setStoryline("")
            thumbnail.setCredentials(directors=[], writers=[], stars=[]);
            thumbnail.setExtras(length="", year="", origin=[], genre=[], theme=[]);
            thumbnail.setGenaratorFunction();
            oContainer.addThumbnail(1, thumbnail);
        }
        containerList.push(oContainer);

        return containerList;

    } 
}