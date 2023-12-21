
//----------
// Generator
//----------
//
class Generator{
    constructor(language_code="en"){
        this.language_code = language_code;
    }

    static startSpinner(){
        $("#spinner").show();
        $("#spinner").attr("width", "100%");    
        $("#spinner").attr("height", "100%");    
    }

    static stopSpinner(){
        $("#spinner").hide();
        $("#spinner").attr("width", "0");    
        $("#spinner").attr("height", "0");    
    }

    showContainers(objScrollSection){
        let refToThis = this
        Generator.startSpinner();

        setTimeout(function () {

            let containerList = refToThis.getContainerList();
            containerList.forEach(oContainer => {
                objScrollSection.addThumbnailContainerObject(oContainer);
            });

            Generator.stopSpinner();

            objScrollSection.focusDefault();

        }, 0);
    }

    getContainerList(){
        throw new Error("Implement getContainerList() method in the " + this.constructor.name + " class!");
    }
}


// --------------
// REST Generator
// --------------
//
class RestGenerator extends Generator{

    static sendRestRequest(rq_method, rq_url){
        let rq_assync = false;
        let result = $.getJSON({method: rq_method, url: rq_url, async: rq_assync, dataType: "json"});
        return result.responseJSON;
    }

    generateThumbnail(hit, type){
        throw new Error("Implement generateThumbnails() method in the " + this.constructor.name + " class!");
    }
    
    getTruncatedTitle(text, max_length){
        let tail = "...";    
        if (text.length > max_length + tail.length)
            text = text.slice(0, max_length) + tail;
        return text;
    }

    generateContainers(requestList){

        let container_list = [];

        for(let request of requestList){
    
            let oContainer = new ObjThumbnailContainer(request["title"]);            
            let request_result = RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"]);

            //for(let index in request_result){
            for(let index=0; index<request_result.length; index++){

                let line = request_result[index];
                let sub_lines = []

                // TODO: check !if(line["level"])
                for(let sub_index=index+1; sub_index<request_result.length; sub_index++){
                    sub_lines.push(request_result[sub_index]);
                }
                let thumbnail = this.generateThumbnail(line, sub_lines);

                oContainer.addThumbnail(line["id"], thumbnail);
            }

            container_list.push(oContainer);
        }

        return container_list;
    }

    getThumbnailTitle(hit){
        let max_length = 20;
        let title = "";

        if(!hit["lang_orig"]){
            hit["lang_orig"] = "";
        }
        
        if(hit["title_on_thumbnail"]){

            // request was not on the original language
            if ( hit["title_req"] != null ){
                title = hit["title_req"];

            // request was on the original langueag or the translated title was configured in the card
            }else if ( hit["title_orig"] != null ){
                title = hit["title_orig"];
            }

            title = this.getTruncatedTitle(title, max_length);
        }

        title = this.getTitleWithPart(hit, title, " ");
        return title;
    }

    getHistoryTitle(hit){
        let max_length = 20;
        let title = "";

        if(!hit["lang_orig"]){
            hit["lang_orig"] = "";
        }

        if ( hit["title_req"] != null ){
            title = hit["title_req"];
        }else if ( hit["title_orig"] != null ){
            title = hit["title_orig"];
        }

        title = this.getTitleWithPart(hit, title, " ");
        return title;

    }

    getMainTitle(hit){
        let title;

        let lang_orig = hit['lang_orig']

        //                                                                requested title    original title    original language    requested language
        // requested = original                                                        ✔               ❌                    ❌                    ✔
        // requested ≠ original requested exist,          original exist               ✔               ✔                    ✔                    ✔
        // requested ≠ original requested does not exist, original exist               ❌               ✔                    ✔                    ❌
        //

        // the requested language is the title's original language => nothing to do
        if(!hit["title_orig"]){
            title = hit["title_req"];

        // there is NO title configure on the requested language => show the original title and the language
        }else if(!hit["title_req"]){
            title = hit["title_orig"]; // + " (" + lang_orig + ")";

        // There IS title configured on the requested language but I want to see the original title as well if it is different
        }else if(always_show_origin_title){
            if(hit["title_req"] != hit["title_orig"]){
                title = hit["title_req"] + " (" + hit["title_orig"] + ")";
            }else{
                title = hit["title_req"];
            }

        // There IS title configured on the requested language and I want to see only this title
        }else{
            title = hit["title_req"];
        }

        title = this.getTitleWithPart(hit, title, " - ");
        return title
    }

    getTitleWithPart(hit, title, separator=" "){
        let result_title = title;
        let show_sequence = hit['title_show_sequence'];
        if(show_sequence != "" && hit['sequence'] && hit['sequence'] > 0){
            let part = translated_titles['sequence'][show_sequence].format("0", hit['sequence']);
        
            if(result_title){
                result_title = result_title + separator + part;
            }
        }
        return result_title;
    }

    static getRandomFileFromDirectory(path, filter){
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

    static getRandomSnapshotPath(source_path){       
        return RestGenerator.getRandomFilePath(source_path, "thumbnails");
    }

    static getRandomScreenshotPath(source_path){   
        return RestGenerator.getRandomFilePath(source_path, "screenshots");  
    }

    static getRandomFilePath(source_path, folder_name){
        let path_to_folder = pathJoin([source_path, folder_name]);
        let file_name = RestGenerator.getRandomFileFromDirectory(path_to_folder, /\.jpg$/);       
        let path = pathJoin([path_to_folder, file_name]);
        return path;
    }

    generateThumbnail(hit, all_hits){
        let refToThis = this;
        let thumbnail = new Thumbnail();

        let thumbnail_title = this.getThumbnailTitle(hit);
        let history_title = this.getHistoryTitle(hit);
        let main_title = this.getMainTitle(hit);

        if(hit["level"]){

            let thumbnail_path = RestGenerator.getRandomSnapshotPath(hit["source_path"]);
            let screenshot_path = RestGenerator.getRandomScreenshotPath(hit["source_path"]);

            thumbnail.setImageSources({thumbnail_src: thumbnail_path, description_src: screenshot_path});
            thumbnail.setTitles({main: main_title, thumb: thumbnail_title});

            thumbnail.setFunctionForSelection({
                "single": 
                    {
                        "menu": 
                            (function(hierarchy_id) {
                                return function() {
                                    return new SubLevelRestGenerator(refToThis.language_code, history_title, hierarchy_id);
                                };
                            })(hit["id"])
                    },
                "continuous": []
            });

        }else{

//console.log("request started")

            // Read the details 
            let card_id = hit["id"];
            let card_request_url = "http://" + host + port + "/collect/media/card_id/" + card_id + "/lang/" + this.language_code
            let card = RestGenerator.sendRestRequest("GET", card_request_url)[0];
    
            // Search for the appendix
            let appendix_list = [];
            if(card["appendix"]){

                let appendix_request_url = "http://" + host + port + "/collect/all/appendix/card_id/" + card_id + "/lang/" +  this.language_code
                let appendix_title_response = RestGenerator.sendRestRequest("GET", appendix_request_url);

                for(let appendix of appendix_title_response){

                    let appendix_dic = {};
                    appendix_dic["id"] = appendix['id'];

                    // This request is to fetch the title
                    if ( appendix["title_req"] != null ){
                        appendix_dic["title"] = appendix["title_req"];
                    }else{
                        appendix_dic["title"] = appendix["title_orig"];
                    }

                    appendix_dic["show"] = appendix["show"];
                    appendix_dic["download"] = appendix["download"];
                    appendix_dic["source_path"] = appendix["source_path"];
                    appendix_dic["media"] = appendix["media"];

                    appendix_list.push(appendix_dic);
                }
            }

            // 'video'
            // 'audio'
            // 'text'
            // 'picture'
            let media;
            let mode;
            let medium_path;
            if("audio" in card["medium"]){
                media=card["medium"]["audio"][0]
                mode = "audio";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                }
            }else if("video" in card["medium"]){
                media=card["medium"]["video"][0]
                mode = "video";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                }
            }else if("picture" in card["medium"]){
                media=card["medium"]["picture"]
                mode = "picture";
                medium_path = [];

                // For picture it creates a list

                for(let medium of media){
                    medium_path.push(pathJoin([card["source_path"], "media", medium]));
                }
            }else if("text" in card["medium"]){
                media=card["medium"]["text"][0]
                mode = "text";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                }
            }else if("pdf" in card["medium"]){
                media=card["medium"]["pdf"][0]
                mode = "pdf";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                }
            }

            let thumbnail_path = RestGenerator.getRandomSnapshotPath(card["source_path"]);
            let screenshot_path = RestGenerator.getRandomScreenshotPath(card["source_path"]);

            thumbnail.setImageSources({thumbnail_src: thumbnail_path, description_src: screenshot_path});
            thumbnail.setTitles({main: main_title, thumb: thumbnail_title});

            thumbnail.setTextCard({storyline:card["storyline"], lyrics:card["lyrics"]});
            thumbnail.setCredentials({directors: card["directors"], writers: card["writers"], stars: card["stars"], actors: card["actors"], voices: card["voices"], hosts: card["hosts"], guests: card["guests"], interviewers: card["interviewers"], interviewees: card["interviewees"], presenters: card["presenters"], lecturers: card["lecturers"], performers: card["performers"], reporters: card["reporters"]});
            thumbnail.setExtras({length: card["length"], date: card["date"], origins: card["origins"], genres: card["genres"], themes: card["themes"]});
            thumbnail.setAppendix(appendix_list);
    
            thumbnail.setFunctionForSelection({
                "single": 
                    {
                        [mode]: 
                            (function(medium_path) {
                                return function() {
                                    return medium_path
                                };
                            })(medium_path),
                        "screenshot_path": screenshot_path
                    },
                "continuous": all_hits
            });


//console.log("request ended")


        }
        return thumbnail;
    }    
}


// ----------------------
// General REST Generator
// ----------------------
//
class GeneralRestGenerator extends RestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        throw new Error("Implement getContainerList() method in the " + this.constructor.name + " class!");
    }
}


// -----------------------
// SubLevel REST Generator
// -----------------------
//
class SubLevelRestGenerator extends  RestGenerator{
    constructor(language_code, container_title, hierarchy_id){
        super(language_code);
        this.container_title = container_title;
        this.hierarchy_id = hierarchy_id;
    }

    getContainerList(){
        let containerList = [];

        let requestList = [
            // I can not tell if it is individual or level
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/child_hierarchy_or_card/id/" + this.hierarchy_id+ "/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}




// =============================================================================

// =========
// MAIN MENU
// =========
//
class MainMenuGenerator extends Generator{  
    getContainerList(){
        let refToThis = this;
        let containerList = [];

        let oContainer = new ObjThumbnailContainer(translated_titles['categories']);

        // Movies
        let thumbnail = new Thumbnail();

        thumbnail.setImageSources({thumbnail_src: "images/categories/movie.jpg", description_src: "images/categories/movie.jpg"});
        thumbnail.setTitles({main: translated_titles['movies'], thumb: translated_titles['movies'], history: translated_titles['movies']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                    (function(movie_type) {
                        return function() {
                            return new MovieMenuGenerator(refToThis.language_code);
                        };
                    })("movies")            
                },
            "continuous": []
        });



        oContainer.addThumbnail(1, thumbnail);

        // Music
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music.jpg", description_src: "images/categories/music.jpg"});
        thumbnail.setTitles({main: translated_titles['music'], thumb: translated_titles['music'], history: translated_titles['music']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicMenuGenerator(refToThis.language_code);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);

        // Radioplay
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/radioplay.jpg", description_src: "images/categories/radioplay.jpg"});
        thumbnail.setTitles({main: translated_titles['radioplay'], thumb: translated_titles['radioplay'], history: translated_titles['radioplay']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new RadioplayMenuGenerator(refToThis.language_code);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);        

        // Audiobook
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/audiobook.jpg", description_src: "images/categories/audiobook.jpg"});
        thumbnail.setTitles({main: translated_titles['audiobook'], thumb: translated_titles['audiobook'], history: translated_titles['audiobook']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new AudiobookMenuGenerator(refToThis.language_code);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);

        // Dia
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/dia.jpg", description_src: "images/categories/dia.jpg"});
        thumbnail.setTitles({main: translated_titles['dia'], thumb: translated_titles['dia'], history: translated_titles['dia']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new DiaMenuGenerator(refToThis.language_code);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);        

        // Entertainment
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/entertainment.jpg", description_src: "images/categories/entertainment.jpg"});
        thumbnail.setTitles({main: translated_titles['entertainments'], thumb: translated_titles['entertainments'], history: translated_titles['entertainments']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(){
                            return function(){
                                return new EntertainmentLevelRestGenerator(refToThis.language_code, translated_titles['entertainment']);
                            }
                        })()
                },
            "continuous": []
        });
        oContainer.addThumbnail(5, thumbnail);

        // Knowledge
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/knowledge.jpg", description_src: "images/categories/knowledge.jpg"});
        thumbnail.setTitles({main: translated_titles['knowledge'], thumb: translated_titles['knowledge'], history: translated_titles['knowledge']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(){
                            return function(){
                                return new KnowledgeLevelRestGenerator(refToThis.language_code, translated_titles['knowledge']);
                            }
                        })()
                },
            "continuous": []
        });
        oContainer.addThumbnail(6, thumbnail);

        containerList.push(oContainer);
 
        return containerList;
    }  
}


// ==========
// MOVIE MENU
// ==========
//
class MovieMenuGenerator extends Generator{  
    getContainerList(){
        let refToThis = this;
        let containerList = [];

        let oContainer = new ObjThumbnailContainer(translated_titles['movies']);

        // Individual
        let thumbnail = new Thumbnail();
        let main,thumb,history,thumbnail_src,description_src;
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_individual.jpg", description_src: "images/categories/movie_individual.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_individual'], thumb: translated_titles['movie_individual'], history: translated_titles['movie_individual']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieCategoriesIndividualRestGenerator(refToThis.language_code);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);

        // Series
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_series.jpg", description_src: "images/categories/movie_series.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_series'], thumb: translated_titles['movie_series'], history: translated_titles['movie_series']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieSerialsLevelRestGenerator(refToThis.language_code, translated_titles['movie_series']);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(2, thumbnail);

        // Sequel
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_sequels.jpg", description_src: "images/categories/movie_sequels.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_sequels'], thumb: translated_titles['movie_sequels'], history: translated_titles['movie_sequels']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieSequelsLevelRestGenerator(refToThis.language_code, translated_titles['movie_sequels']);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(3, thumbnail);

        // Remake
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_remakes.jpg", description_src: "images/categories/movie_remakes.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_remakes'], thumb: translated_titles['movie_remakes'], history: translated_titles['movie_remakes']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieRemakesLevelRestGenerator(refToThis.language_code, translated_titles['movie_remakes']);
                            };
                        })("movies")                    
                },
            "continuous": []
        });
        oContainer.addThumbnail(3, thumbnail);
        
        // Documentaries
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_documentaries.jpg", description_src: "images/categories/movie_documentaries.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_documentaries'], thumb: translated_titles['movie_documentaries'], history: translated_titles['movie_documentaries']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieDocumentariesIndividualRestGenerator(refToThis.language_code, translated_titles['movie_documentaries']);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(4, thumbnail);
        
        containerList.push(oContainer);
 
        return containerList;
    }  
}


//class MovieCategoriesIndividualRestGenerator extends  IndividualRestGenerator{
class MovieCategoriesIndividualRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: translated_genre_movie['drama'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/drama/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_genre_movie['comedy'],      rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/comedy/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_genre_movie['satire'],      rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/satire/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_genre_movie['scifi'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/scifi/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_genre_movie['western'],     rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/western/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_genre_movie['war'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/war/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_genre_movie['documentary'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/documentary/theme/*/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['apocalypse'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/apocalypse/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['conspiracy'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/conspiracy/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['drog'],             rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/drog/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['maffia'],           rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/maffia/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['broker'],           rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/broker/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['media'],            rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/media/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: translated_themes['evil'],             rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/evil/origin/*/not_origin/hu/decade/*/lang/" +  this.language_code},
            {title: "60s",                                 rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/*/origin/*/not_origin/hu/decade/60s/lang/" +  this.language_code},
            {title: translated_titles['movie_hungarian'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/genre/*/theme/*/origin/hu/not_origin/*/decade/*/lang/" +  this.language_code},

//            {title: "Luc Besson",                          rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/movie/director/Luc Besson/actor/*/writer/*/decade/*/lang/" +  this.language_code},


        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


//class MovieSerialsLevelRestGenerator extends  LevelRestGenerator{
class MovieSerialsLevelRestGenerator extends  GeneralRestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/series/category/movie/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


//class MovieSequelsLevelRestGenerator extends  LevelRestGenerator{
class MovieSequelsLevelRestGenerator extends  GeneralRestGenerator{
    
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/sequel/category/movie/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


//class MovieRemakesLevelRestGenerator extends  LevelRestGenerator{
class MovieRemakesLevelRestGenerator extends  GeneralRestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/remake/category/movie/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


//class MovieDocumentariesIndividualRestGenerator extends  IndividualRestGenerator{
class MovieDocumentariesIndividualRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: translated_genre_movie['movie_documentaries'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/standalone/movies/genre/documentary/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ==========
// MUSIC MENU
// ==========
//
class MusicMenuGenerator extends Generator{  
    getContainerList(){
        let refToThis = this;
        let containerList = [];

        let oContainer = new ObjThumbnailContainer(translated_titles['music']);

        // Video music
        let thumbnail = new Thumbnail();
        let main,thumb,history,thumbnail_src,description_src;
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_video.jpg", description_src: "images/categories/music_video.jpg"});
        thumbnail.setTitles({main: translated_titles['music_video'], thumb: translated_titles['music_video'], history: translated_titles['music_video']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(blabla){
                            return function(){
                                return new MusicVideoLevelRestGenerator(refToThis.language_code, translated_titles['music_video']);
                            }
                        })("blabla")                    
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);

        // Audio music
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_audio.jpg", description_src: "images/categories/music_audio.jpg"});
        thumbnail.setTitles({main: translated_titles['music_audio'], thumb: translated_titles['music_audio'], history: translated_titles['music_audio']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                    (function(){
                        return function(){
                            return new MusicAudioLevelRestGenerator(refToThis.language_code, translated_titles['music_audio']);
                        }
                    })()                    
                },
            "continuous": []
        });
        oContainer.addThumbnail(2, thumbnail);
 
        containerList.push(oContainer);
 
        return containerList;
    }  
}

//class MusicVideoLevelRestGenerator extends  LevelRestGenerator{
class MusicVideoLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: "60s",                                 rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/*/not_origin/hu/decade/60s/lang/" +  this.language_code},
            {title: "70s",                                 rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/*/not_origin/hu/decade/70s/lang/" +  this.language_code},
            {title: "80s",                                 rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/*/not_origin/hu/decade/80s/lang/" +  this.language_code},
            {title: "90s",                                 rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/*/not_origin/hu/decade/90s/lang/" +  this.language_code},
            {title: "2000s",                               rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/*/not_origin/hu/decade/2000s/lang/" +  this.language_code},
            {title: "2010s",                               rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/*/not_origin/hu/decade/2010s/lang/" +  this.language_code},
            {title: translated_titles['music_hungarian'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_video/genre/*/theme/*/origin/hu/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

//class MusicAudioLevelRestGenerator extends  LevelRestGenerator{
class MusicAudioLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: "70s",  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_audio/genre/*/theme/*/origin/*/not_origin/*/decade/70s/lang/" +  this.language_code},
            {title: "80s",  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/band/category/music_audio/genre/*/theme/*/origin/*/not_origin/*/decade/80s/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }

}


// ==============
// Radioplay MENU
// ==============
//
//class RadioplayMenuGenerator extends  IndividualRestGenerator{
class RadioplayMenuGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];
        let requestList = [
            {title: translated_titles['radioplay'],  rq_method: "GET", rq_url: "http://" + host + "/collect/general/standalone/category/radio_play/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ==============
// Audiobook MENU
// ==============
//
//class AudiobookMenuGenerator extends  IndividualRestGenerator{
class AudiobookMenuGenerator extends  GeneralRestGenerator{


    getContainerList(){
        let containerList = [];
        let requestList = [
            {title: translated_titles['audiobook'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/audiobook/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['audiobook'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/audiobook/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ========
// Dia MENU
// ========
//
//class DiaMenuGenerator extends  IndividualRestGenerator{
class DiaMenuGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];
        let requestList = [
            {title: translated_titles['dia'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/dia/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ==================
// Entertainment MENU
// ==================
//
//class EntertainmentLevelRestGenerator extends  LevelRestGenerator{
class EntertainmentLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/entertainment/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
           ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


// ==============
// Knowledge MENU
// ==============
//
//class KnowledgeLevelRestGenerator extends  LevelRestGenerator{
class KnowledgeLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/knowledge/genre/*/theme/*/origin/*/not_origin/*/decade/*/lang/" +  this.language_code},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

