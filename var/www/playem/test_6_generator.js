class Generator{
    constructor(language_code="en"){
         this.language_code = language_code;
    }

    // TODO: why the Generater generates this. Change it
    generateScrollSection(history={text:"", link:""}){
        let oScrollSection = new ObjScrollSection(this, history);
        oScrollSection.focusDefault();
        return oScrollSection;
    }

    sendRestRequest(rq_method, rq_url){
        let rq_assync = false;
        let result = $.getJSON({method: rq_method, url: rq_url, async: rq_assync, dataType: "json"});
        return result.responseJSON;
    }

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
    getRandomFileFromDirectory(path, filter){
        let file_list = [];
        let rawText = $.ajax({url: path, async: false}).responseText;
        $(rawText).find('tr > td > a').not(':first').each(function(){                          
            let file_name = $(this).attr("href");
            if(filter.test(file_name))
                file_list.push(file_name);
        });
        let random_file = undefined;
        if(file_list.length)
            random_file = file_list[Math.floor(Math.random()*file_list.length)];
        return random_file;
    }

    getTruncatedTitle(text, max_length){
        let tail = "...";
    
        if (text.length > max_length + tail.length)
            text = text.slice(0, max_length) + tail;
        return text;
    }

    generateContainers(requestList){

        let max_length = 20;
        let container_list = [];

        for(let request of requestList){
    
            let oContainer = new ObjThumbnailContainer(request["title"]);
            let request_result = this.sendRestRequest(request["rq_method"], request["rq_url"]);

            for(let line of request_result){

                if(!line["lang_orig"]){
                    line["lang_orig"] = "";
                }
                let short_title = "";
                if ( line["title_req"] != null ){
                    short_title = line["title_req"];
                }else if ( line["title_orig"] != null ){
                    short_title = line["title_orig"];
                }

                short_title = this.getTruncatedTitle(short_title, max_length);
                let thumbnail_file = this.getRandomFileFromDirectory(line["source_path"] + "/thumbnails", /\.jpg$/);
                let screenshot_file = this.getRandomFileFromDirectory(line["source_path"] + "/screenshots", /\.jpg$/);


                let path = line["source_path"] + "/card.yaml";                                
                let rawText = $.ajax({url: path, async: false}).responseText;
                let yaml_card = jsyaml.load(rawText);


                let thumbnail = new Thumbnail();
                let thumbnail_src, description_src,lang,original,translated,thumb,directors,writers,stars,length,year,origin,genre,theme
                thumbnail.setImageSources(thumbnail_src=line["source_path"] + "/thumbnails/" + thumbnail_file, description_src=line["source_path"] + "/screenshots/" + screenshot_file);
                thumbnail.setTitles(lang=line["lang_orig"], original=line["title_orig"], translated=line["title_req"], thumb=short_title);
thumbnail.setStoryline(yaml_card["storylines"]["hu"]);
                thumbnail.setCredentials(directors=yaml_card["directors"], writers=yaml_card["writers"], stars=yaml_card["stars"]);
                thumbnail.setExtras(length=yaml_card["length"], year=yaml_card["year"], origin=yaml_card["origin"], genre=yaml_card["genre"], theme=yaml_card["theme"]);
                thumbnail.setGenaratorFunction();
                oContainer.addThumbnail(line["id"], thumbnail);
            }
            container_list.push(oContainer);
        }

        return container_list;
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
        thumbnail.setGenaratorFunction({"menu": 
            (function(movie_type) {
                return function() {
                    return new MovieMenuGenerator(refToThis.languageCode)
                };
            })("movies")});
        oContainer.addThumbnail(1, thumbnail);

        thumbnail = new Thumbnail();
        thumbnail.setImageSources(thumbnail_src="images/categories/series.jpg", description_src="images/categories/series.jpg");
        thumbnail.setTitles(lang="hu", original="Movie Series", translated="Movie Series", thumb="Movie Series", history="Movie Series");
        thumbnail.setGenaratorFunction(function(){refToThis.viewMovie()});
        oContainer.addThumbnail(2, thumbnail);

        thumbnail = new Thumbnail();
        thumbnail.setImageSources(thumbnail_src="images/categories/music_video.jpg", description_src="images/categories/music_video.jpg");
        thumbnail.setTitles(lang="hu", original="Music Video", translated="Music Video", thumb="Music Video", history="Music Video");
        thumbnail.setGenaratorFunction(function(){refToThis.viewMovie()});
        oContainer.addThumbnail(3, thumbnail);

        thumbnail = new Thumbnail();
        thumbnail.setImageSources(thumbnail_src="images/categories/music_audio.jpg", description_src="images/categories/music_audio.jpg");
        thumbnail.setTitles(lang="hu", original="Music Audio", translated="Music Audio", thumb="Music Audio", history="Music Audio");
        thumbnail.setGenaratorFunction(function(){refToThis.viewMovie()});
        oContainer.addThumbnail(3, thumbnail);

        containerList.push(oContainer);
 
        return containerList;
    }
}


class MovieMenuGenerator extends Generator{
 
    getContainerList(){

        let refToThis = this;
        let containerList = [];


        let requestList = [
            {title: "Drama",  rq_method: "GET", rq_url: "http://192.168.0.21/collect/standalone/movies/genre/drama/lang/" +  this.language_code},
            {title: "Comedy", rq_url:    "GET", rq_url: "http://192.168.0.21/collect/standalone/movies/genre/comedy/lang/" + this.language_code},
            {title: "Sci-fi", rq_url:    "GET", rq_url: "http://192.168.0.21/collect/standalone/movies/genre/scifi/lang/" +  this.language_code}
        ];

        containerList = this.generateContainers(requestList);

        return containerList;
    } 
}