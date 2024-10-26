
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

    generateThumbnail(filter, play_list){
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
    
            // Build up the request url out of filter
            for (const [key, value] of Object.entries(request['filter'])) {
                request['rq_url'] = request['rq_url'].format(key, value);
            }

            let oContainer = new ObjThumbnailContainer(request["title"]);            
            let request_result = RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"]);

            //for(let index in request_result){
            for(let index=0; index<request_result.length; index++){

                let line = request_result[index];
                let play_list = [];

                //
                // Collects all media which needs to continuous play
                //
                for(let sub_index=index; sub_index<request_result.length; sub_index++){
                    play_list.push(request_result[sub_index]);
                }

                let thumbnail = this.generateThumbnail(request['filter'], play_list);

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

        title = RestGenerator.getTitleWithPart(hit, title, " ");
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

        title = RestGenerator.getTitleWithPart(hit, title, " ");
        return title;

    }

    static getMainTitle(hit){
        let title;

//        let lang_orig = hit['lang_orig']

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
        }else if(user_data['always_show_original_title']){
            if(hit["title_req"] != hit["title_orig"]){
                title = hit["title_req"] + " (" + hit["title_orig"] + ")";
            }else{
                title = hit["title_req"];
            }

        // There IS title configured on the requested language and I want to see only this title
        }else{
            title = hit["title_req"];
        }

        title = RestGenerator.getTitleWithPart(hit, title, " - ");
//        title = this.getTitleWithPart(hit, title, " - ");
        return title
    }

    static getTitleWithPart(hit, title, separator=" "){
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

    static getRandomFileFromDirectory(path,filter){
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
        return RestGenerator.getRandomFilePath(source_path, "thumbnails", "images/thumbnails/thumbnail_empty_460x600.jpg");
    }

    static getRandomScreenshotPath(source_path){   
        return RestGenerator.getRandomFilePath(source_path, "screenshots", "images/thumbnails/screenshot_empty_1100x500.jpg");  
    }

    static getRandomFilePath(source_path, folder_name, default_path){
        let path_to_folder = pathJoin([source_path, folder_name]);
        let file_name = RestGenerator.getRandomFileFromDirectory(path_to_folder, /\.jpg$/);
        let path;
        if(file_name == undefined){
            path=default_path;
        }else{
            path = pathJoin([path_to_folder, file_name]);
        }
        return path;
    }

    generateThumbnail(filters, play_list){
        let hit = play_list[0];

        let refToThis = this;
        let thumbnail = new Thumbnail();

        let thumbnail_title = this.getThumbnailTitle(hit);
        let history_title = this.getHistoryTitle(hit);
        let main_title = RestGenerator.getMainTitle(hit);

//        let card_id = hit["id"];

        // If any numbers of appendix belong to the card (regardles of it is media card or level)
        if(hit["appendix"]){
 
            let appendix_list = [];
            for(let appendix of hit["appendix"]){

                let appendix_dic = {};
                appendix_dic["id"] = appendix['id'];

                if ( appendix["rt"]){
                    appendix_dic["title"] = appendix["rt"];
                }else{
                    appendix_dic["title"] = appendix["ot"];
                }

                appendix_dic["show"] = appendix["sw"];
                appendix_dic["download"] = appendix["dl"];
                appendix_dic["source_path"] = appendix["sp"];
                let media = {};
                media[appendix["mt"]] = appendix["cm"];
                appendix_dic["media"] = media;
                appendix_list.push(appendix_dic);                
            }

            // save the appendix list
            thumbnail.setAppendix(appendix_list);
        }

        if(hit["level"]){

            let thumbnail_path = RestGenerator.getRandomSnapshotPath(hit["source_path"]);
            let screenshot_path = RestGenerator.getRandomScreenshotPath(hit["source_path"]);

            thumbnail.setImageSources({thumbnail_src: thumbnail_path, description_src: screenshot_path});
            thumbnail.setTitles({main: main_title, thumb: thumbnail_title});

            thumbnail.setTextCard({storyline:hit["storyline"], lyrics:hit["lyrics"]});
            thumbnail.setExtras({length: hit["length"], date: hit["date"], origins: hit["origins"], genres: hit["genres"], themes: hit["themes"], level: hit["level"] });

            thumbnail.setFunctionForSelection({
                "single": 
                    {
                        "menu": 
                            (function(hierarchy_id, filters) {
                                return function() {
                                    return new SubLevelRestGenerator(refToThis.language_code, history_title, hierarchy_id, filters);
                                };
                            })(hit["id"], filters )
                    },
                "continuous": []
            });

        }else{

            let card = hit

            // 'video'
            // 'audio'
            // 'text'
            // 'picture'
            let media;
            let mode;
            let medium_path;
            let medium_dict = {};

            let thumbnail_path = RestGenerator.getRandomSnapshotPath(card["source_path"]);
            let screenshot_path = RestGenerator.getRandomScreenshotPath(card["source_path"]);

            if("audio" in card["medium"]){
                media=card["medium"]["audio"][0]
                mode = "audio";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                    medium_dict["medium_path"] = medium_path;
                    medium_dict["screenshot_path"] = screenshot_path;
                    medium_dict["card_id"] = card["id"];
                    medium_dict["net_start_time"] = card["net_start_time"];
                    medium_dict["net_stop_time"] = card["net_stop_time"];
                }
            }else if("video" in card["medium"]){
                media=card["medium"]["video"][0]
                mode = "video";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                    medium_dict["medium_path"] = medium_path;
                    medium_dict["screenshot_path"] = null;
                    medium_dict["card_id"] = card["id"];
                    medium_dict["net_start_time"] = card["net_start_time"];
                    medium_dict["net_stop_time"] = card["net_stop_time"];
                }
            }else if("picture" in card["medium"]){
                media=card["medium"]["picture"]
                mode = "picture";
                medium_path = [];

                // For picture it creates a list

                for(let medium of media){
                    medium_path.push(pathJoin([card["source_path"], "media", medium])); //*
                }
                medium_dict["medium_path_list"] = medium_path;
                medium_dict["screenshot_path"] = screenshot_path;
                medium_dict["card_id"] = card["id"];

            }else if("text" in card["medium"]){
                media=card["medium"]["text"][0]
                mode = "text";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                    medium_dict["medium_path"] = medium_path;
                    medium_dict["screenshot_path"] = screenshot_path;
                    medium_dict["card_id"] = card["id"];
                }
            }else if("pdf" in card["medium"]){
                media=card["medium"]["pdf"][0]
                mode = "pdf";
                if(media){
                    medium_path = pathJoin([card["source_path"], "media", media]);
                    medium_dict["medium_path"] = medium_path;
                    medium_dict["screenshot_path"] = screenshot_path;
                    medium_dict["card_id"] = card["id"];
                }
            }

            thumbnail.setImageSources({thumbnail_src: thumbnail_path, description_src: screenshot_path});
            thumbnail.setTitles({main: main_title, thumb: thumbnail_title});

            thumbnail.setTextCard({storyline:card["storyline"], lyrics:card["lyrics"]});
            thumbnail.setCredentials({directors: card["directors"], writers: card["writers"], stars: card["stars"], actors: card["actors"], voices: card["voices"], hosts: card["hosts"], guests: card["guests"], interviewers: card["interviewers"], interviewees: card["interviewees"], presenters: card["presenters"], lecturers: card["lecturers"], performers: card["performers"], reporters: card["reporters"]});

            // TODO: fix it
            // This is not the best choice to store 'medium_path' and 'download' in the 'extras', but that is what I choose. It could be changed
            thumbnail.setExtras({medium_path: medium_path, download: card["download"], length: card["length"], full_time: card["full_time"],net_start_time: card["net_start_time"], net_stop_time: card["net_stop_time"], date: card["date"], origins: card["origins"], genres: card["genres"], themes: card["themes"], level: card["level"], recent_state: hit["recent_state"], 'rate': hit['rate'], 'skip_continuous_play': hit['skip_continuous_play'], 'tags': hit['tags']});
    
            thumbnail.setFunctionForSelection({
                "single": 
                    {
                        [mode]: null,
                        "medium_dict": medium_dict
                    },
                "continuous": play_list
            });
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
    constructor(language_code, container_title, hierarchy_id, filters){
        super(language_code);
        this.container_title = container_title;
        this.hierarchy_id = hierarchy_id;
        this.filters = filters;
    }

    getContainerList(){
        let containerList = [];

        // TODO: we just added the filter in the constructor. Now I add it again

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/next/mixed/card_id/" + this.hierarchy_id + "/category/{category}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: this.filters},
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
        oContainer.addThumbnail(2, thumbnail);

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
        oContainer.addThumbnail(3, thumbnail);        

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
        oContainer.addThumbnail(4, thumbnail);

        // EBook
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/ebook.jpg", description_src: "images/categories/ebook.jpg"});
        thumbnail.setTitles({main: translated_titles['ebook'], thumb: translated_titles['ebook'], history: translated_titles['ebook']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new EbookMenuGenerator(refToThis.language_code);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(5, thumbnail);

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
        oContainer.addThumbnail(6, thumbnail);        

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
        oContainer.addThumbnail(7, thumbnail);

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
        oContainer.addThumbnail(8, thumbnail);

        // Personal
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/personal.jpg", description_src: "images/categories/personal.jpg"});
        thumbnail.setTitles({main: translated_titles['personal'], thumb: translated_titles['personal'], history: translated_titles['personal']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(){
                            return function(){
                                return new PersonalLevelRestGenerator(refToThis.language_code, translated_titles['personal']);
                            }
                        })()
                },
            "continuous": []
        });
        oContainer.addThumbnail(9, thumbnail);

        containerList.push(oContainer);
 
        return containerList;
    }  
}


// ==========
// MOVIE MENU
// ==========
//
// I changed the parent because I need mixed content inside (normal and rest)
class MovieMenuGenerator extends GeneralRestGenerator{    
    getContainerList(){
        let refToThis = this;
        let containerList = [];

        let oContainer = new ObjThumbnailContainer(translated_titles['movies']);

        // Mixed
        let thumbnail = new Thumbnail();
        let main,thumb,history,thumbnail_src,description_src;
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_mixed.jpg", description_src: "images/categories/movie_mixed.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_mixed'], thumb: translated_titles['movie_mixed'], history: translated_titles['movie_mixed']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieFilterRestGenerator(refToThis.language_code);
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
        oContainer.addThumbnail(4, thumbnail);

        // Playlist
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_playlist.jpg", description_src: "images/categories/movie_playlist.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_playlists'], thumb: translated_titles['movie_playlists'], history: translated_titles['movie_playlists']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MoviePlaylistsRestGenerator(refToThis.language_code, translated_titles['movie_playlists']);
                            };
                        })("movies")
                },
            "continuous": []
        });
        oContainer.addThumbnail(5, thumbnail);


//        // Continue playing Movie
//        thumbnail = new Thumbnail();
//        thumbnail.setImageSources({thumbnail_src: "images/categories/continue_playing.jpg", description_src: "images/categories/continue_playing.jpg"});
//        thumbnail.setTitles({main: translated_titles['continue_playing_movie'], thumb: translated_titles['continue_playing_movie'], history: translated_titles['continue_playing_movie']});
//        thumbnail.setFunctionForSelection({
//            "single": 
//                {
//                    "menu": 
//                        (function(movie_type) {
//                            return function() {
//                                return new MovieContinuePlayingRestGenerator(refToThis.language_code, translated_titles['continue_playing_movie']);
//                            };
//                        })("movies")
//                },
//            "continuous": []
//        });
//        oContainerContinuePlaying.addThumbnail(1, thumbnail);


        // ---

        containerList.push(oContainer);
 
        return containerList;
    }  
}






















class MovieFilterRestGenerator extends GeneralRestGenerator{    
    getContainerList(){
        let refToThis = this;
        let containerList = [];

        let oContainer = new ObjThumbnailContainer(translated_titles['movie_filter']);

        // By Genre
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_by_genre.jpg", description_src: "images/categories/movie_by_genre.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_by_genre'], thumb: translated_titles['movie_by_genre'], history: translated_titles['movie_by_genre']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieFilterGenreRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);

        // By Theme
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_by_theme.jpg", description_src: "images/categories/movie_by_theme.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_by_theme'], thumb: translated_titles['movie_by_theme'], history: translated_titles['movie_by_theme']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieFilterThemeRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainer.addThumbnail(2, thumbnail);

        // By Director
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_by_director.jpg", description_src: "images/categories/movie_by_director.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_by_director'], thumb: translated_titles['movie_by_director'], history: translated_titles['movie_by_director']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieFilterDirectorRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainer.addThumbnail(3, thumbnail);

        // By Actor
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_by_actor.jpg", description_src: "images/categories/movie_by_actor.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_by_actor'], thumb: translated_titles['movie_by_actor'], history: translated_titles['movie_by_actor']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieFilterActorRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainer.addThumbnail(3, thumbnail);
        // ---

        containerList.push(oContainer);
 
        return containerList;
    }
}


class MovieFilterGenreRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let filter_drama       = {category: 'movie', level: '*', genres:'drama',                  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_scifi       = {category: 'movie', level: '*', genres:'scifi',                  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_fantasy     = {category: 'movie', level: '*', genres:'fantasy',                themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_comedy      = {category: 'movie', level: '*', genres:'comedy_AND__NOT_teen',   themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_teen        = {category: 'movie', level: '*', genres:'teen',                   themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_satire      = {category: 'movie', level: '*', genres:'satire',                 themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_crime       = {category: 'movie', level: '*', genres:'crime',                  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_action      = {category: 'movie', level: '*', genres:'action',                 themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_thriller    = {category: 'movie', level: '*', genres:'thriller',               themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_western     = {category: 'movie', level: '*', genres:'western',                themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_war         = {category: 'movie', level: '*', genres:'war',                    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_music       = {category: 'movie', level: '*', genres:'music',                  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_documentary = {category: 'movie', level: '*', genres:'documentary',            themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_trash       = {category: 'movie', level: '*', genres:'trash',                  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_movie['drama'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_drama},
            {title: translated_genre_movie['scifi'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_scifi},
            {title: translated_genre_movie['fantasy'],     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_fantasy},
            {title: translated_genre_movie['comedy'],      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_comedy},
            {title: translated_genre_movie['teen'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_teen},
            {title: translated_genre_movie['satire'],      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_satire},
            {title: translated_genre_movie['crime'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_crime},
            {title: translated_genre_movie['action'],      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_action},
            {title: translated_genre_movie['thriller'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_thriller},
            {title: translated_genre_movie['western'],     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_western},
            {title: translated_genre_movie['war'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_war},
            {title: translated_genre_movie['music'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_music},
            {title: translated_genre_movie['documentary'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_documentary},
            {title: translated_genre_movie['trash'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_trash},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterThemeRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let filter_apocalypse    = {category: 'movie', level: '*', genres:'*', themes: 'apocalypse', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_dystopia      = {category: 'movie', level: '*', genres:'*', themes: 'dystopia',   directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_conspiracy    = {category: 'movie', level: '*', genres:'*', themes: 'conspiracy', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_drog          = {category: 'movie', level: '*', genres:'*', themes: 'drog',       directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_maffia        = {category: 'movie', level: '*', genres:'*', themes: 'maffia',     directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_broker        = {category: 'movie', level: '*', genres:'*', themes: 'broker',     directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_media         = {category: 'movie', level: '*', genres:'*', themes: 'media',      directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_evil          = {category: 'movie', level: '*', genres:'*', themes: 'evil',       directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_alien         = {category: 'movie', level: '*', genres:'*', themes: 'alien',      directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_revenge       = {category: 'movie', level: '*', genres:'*', themes: 'revenge',    directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_themes['apocalypse'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_apocalypse},
            {title: translated_themes['dystopia'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_dystopia},
            {title: translated_themes['conspiracy'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_conspiracy},
            {title: translated_themes['drog'],             rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_drog},
            {title: translated_themes['maffia'],           rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_maffia},
            {title: translated_themes['broker'],           rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_broker},
            {title: translated_themes['media'],            rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_media},
            {title: translated_themes['evil'],             rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_evil},
            {title: translated_themes['alien'],            rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alien},
            {title: translated_themes['revenge'],          rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_revenge},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterDirectorRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let filter_luc_besson      = {category: 'movie', level: '*', genres:'*', themes: '*', directors: 'Luc Besson',      actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_david_lynch     = {category: 'movie', level: '*', genres:'*', themes: '*', directors: 'David Lynch',     actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_woody_allen     = {category: 'movie', level: '*', genres:'*', themes: '*', directors: 'Woody Allen',     actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_john_carpenter  = {category: 'movie', level: '*', genres:'*', themes: '*', directors: 'John Carpenter',  actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_stanley_kubrick = {category: 'movie', level: '*', genres:'*', themes: '*', directors: 'Stanley Kubrick', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_terry_gilliam   = {category: 'movie', level: '*', genres:'*', themes: '*', directors: 'Terry Gilliam',   actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: "Luc Besson",       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_luc_besson},
            {title: "David Lynch",      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_david_lynch},
            {title: "Woody Allen",      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_woody_allen},
            {title: "John Carpenter",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_john_carpenter},
            {title: "Stanley Kubrick",  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_stanley_kubrick},
            {title: "Terry Gilliam",    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_terry_gilliam},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterActorRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let filter_robert_de_Niro    = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Robert De Niro',      lecturers: '*', origins: '*', decade: '*'};
        let filter_al_pacino         = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Al Pacino',           lecturers: '*', origins: '*', decade: '*'};
        let filter_brad_pitt         = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Brad Pitt',           lecturers: '*', origins: '*', decade: '*'};
        let filter_johnny_depp       = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Johnny Depp',         lecturers: '*', origins: '*', decade: '*'};
        let filter_sigourney_weaver  = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Sigourney Weaver',    lecturers: '*', origins: '*', decade: '*'};
        let filter_benicio_del_toro  = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Benicio Del Toro',    lecturers: '*', origins: '*', decade: '*'};
        let filter_nicole_kidman     = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Nicole Kidman',       lecturers: '*', origins: '*', decade: '*'};
        let filter_robert_loggia     = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Robert Loggia',       lecturers: '*', origins: '*', decade: '*'};
        let filter_clint_eastwood    = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Clint Eastwood',      lecturers: '*', origins: '*', decade: '*'};
        let filter_gene_hackman      = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Gene Hackman',        lecturers: '*', origins: '*', decade: '*'};
        let filter_michael_douglas   = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Michael Douglas',     lecturers: '*', origins: '*', decade: '*'};
        let filter_peter_greene      = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Peter Greene',        lecturers: '*', origins: '*', decade: '*'};
        let filter_kevin_spacey      = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Kevin Spacey',        lecturers: '*', origins: '*', decade: '*'};
        let filter_joaquin_phoenix   = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Joaquin Phoenix',     lecturers: '*', origins: '*', decade: '*'};
        let filter_jonah_hill        = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Jonah Hill',          lecturers: '*', origins: '*', decade: '*'};
        let filter_simon_pegg        = {category: 'movie', level: '*', genres:'*', themes: '*', directors: '*', actors: 'Simon Pegg',          lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: "Robert De Niro",      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_robert_de_Niro},
            {title: "Al Pacino",           rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_al_pacino},
            {title: "Brad Pitt",           rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_brad_pitt},
            {title: "Johnny Depp",         rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_johnny_depp},
            {title: "Sigourney Weaver",    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_sigourney_weaver},
            {title: "Benicio Del Toro",    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_benicio_del_toro},
            {title: "Nicole Kidman",       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_nicole_kidman},
            {title: "Robert Loggia",       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_robert_loggia},
            {title: "Clint Eastwood",      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_clint_eastwood},
            {title: "Gene Hackman",        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_gene_hackman},
            {title: "Michael Douglas",     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_michael_douglas},
            {title: "Peter Greene",        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_peter_greene},
            {title: "Kevin Spacey",        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_kevin_spacey},
            {title: "Joaquin Phoenix",     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_joaquin_phoenix},
            {title: "Jonah Hill",          rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_jonah_hill},
            {title: "Simon Pegg",          rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_simon_pegg},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}











class MovieSerialsLevelRestGenerator extends  GeneralRestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let series_tail_filter         = {category: 'movie', level: 'series', genres:'tale',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let series_comedy_filter       = {category: 'movie', level: 'series', genres:'comedy',      themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let series_drama_filter        = {category: 'movie', level: 'series', genres:'drama',       themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let series_thriller_filter     = {category: 'movie', level: 'series', genres:'thriller',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let series_scifi_filter        = {category: 'movie', level: 'series', genres:'scifi',       themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let series_documentary_filter  = {category: 'movie', level: 'series', genres:'documentary', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        // let series_filter        = {category: 'movie', level: 'series', genres:'*',      themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title + "-" + translated_genre_movie['tale'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_tail_filter},
            {title: this.container_title + "-" + translated_genre_movie['drama'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_drama_filter},
            {title: this.container_title + "-" + translated_genre_movie['comedy'],      rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_comedy_filter},
            {title: this.container_title + "-" + translated_genre_movie['thriller'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_thriller_filter},           
            {title: this.container_title + "-" + translated_genre_movie['scifi'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_scifi_filter},
            {title: this.container_title + "-" + translated_genre_movie['documentary'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_documentary_filter},

        //    {title: this.container_title + "-", rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_filter}
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}










class MovieSequelsLevelRestGenerator extends  GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let sequel_drama_filter    = {category: 'movie', level: 'sequel', genres:'drama',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let sequel_comedy_filter   = {category: 'movie', level: 'sequel', genres:'comedy',   themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let sequel_thriller_filter = {category: 'movie', level: 'sequel', genres:'thriller', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let sequel_action_filter   = {category: 'movie', level: 'sequel', genres:'action',   themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let sequel_scifi_filter    = {category: 'movie', level: 'sequel', genres:'scifi',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        // let sequel_filter = {category: 'movie', level: 'sequel', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title + "-" + translated_genre_movie['drama'],     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_drama_filter},
            {title: this.container_title + "-" + translated_genre_movie['comedy'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_comedy_filter},
            {title: this.container_title + "-" + translated_genre_movie['thriller'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_thriller_filter},
            {title: this.container_title + "-" + translated_genre_movie['action'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_action_filter},
            {title: this.container_title + "-" + translated_genre_movie['scifi'],     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_scifi_filter},

        //    {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_filter}
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}











class MovieRemakesLevelRestGenerator extends GeneralRestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let remake_filter = {category: 'movie', level: 'remake', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: remake_filter}
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}



class MoviePlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let interrupted_filter =  {category: 'movie', playlist: 'interrupted',  tags: '*', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let last_watched_filter = {category: 'movie', playlist: 'last_watched', tags: '*', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let most_watched_filter = {category: 'movie', playlist: 'most_watched', tags: '*', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['movie_interrupted'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: interrupted_filter},
            {title: translated_titles['movie_last_watched'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: last_watched_filter},
            {title: translated_titles['movie_most_watched'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: most_watched_filter}
        ];


        // Get the existion TAGs
        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/personal/tag/get";
        let rq_assync = false;
        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync});
        if(response.status == 200 && response.responseJSON["result"]){
            for (let data_dict of response.responseJSON["data"]){

                let filter = {};
                filter["category"] = 'movie';
                filter["playlist"] = '*';
                filter["tags"] = data_dict["name"];
                filter["level"] = '*';
                filter["genres"] = '*';
                filter["themes"] = '*';
                filter["directors"] = '*';
                filter["actors"] = '*';
                filter["lecturers"] = '*';
                filter["origins"] = '*';
                filter["origins"] = '*';
                filter["decade"] = '*';

                let request = {};
                request["title"] = data_dict["name"];
                request["rq_method"] = 'GET';
                request["rq_url"] = "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code;
                request["filter"] = filter;
                requestList.push(request);
            }
        }

        containerList = this.generateContainers(requestList);
        return containerList;
    }

}


    



// ==========
//
// MUSIC MENU
//
// ==========
//
class MusicMenuGenerator extends Generator{  
    getContainerList(){
        let refToThis = this;
        let containerList = [];

        // === Music-Video ===

        let oContainerVideo = new ObjThumbnailContainer(translated_titles['music_video']);

        // Decade
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_by_decade.jpg", description_src: "images/categories/music_by_decade.jpg"});
        thumbnail.setTitles({main: translated_titles['music_by_decade'], thumb: translated_titles['music_by_decade'], history: translated_titles['music_by_decade']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterDecadeRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerVideo.addThumbnail(1, thumbnail);

        // Genre
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_by_genre.jpg", description_src: "images/categories/music_by_genre.jpg"});
        thumbnail.setTitles({main: translated_titles['music_by_genre'], thumb: translated_titles['music_by_genre'], history: translated_titles['music_by_genre']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterGenreRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerVideo.addThumbnail(1, thumbnail);        

        // ABC
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_by_band_abc.jpg", description_src: "images/categories/music_by_band_abc.jpg"});
        thumbnail.setTitles({main: translated_titles['music_by_band_abc'], thumb: translated_titles['music_by_band_abc'], history: translated_titles['music_by_band_abc']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterGroupAbcRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerVideo.addThumbnail(1, thumbnail);        

        // === Music-Audio ===

        let oContainerAudio = new ObjThumbnailContainer(translated_titles['music_audio']);

        // Decade
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_by_decade.jpg", description_src: "images/categories/music_by_decade.jpg"});
        thumbnail.setTitles({main: translated_titles['music_by_decade'], thumb: translated_titles['music_by_decade'], history: translated_titles['music_by_decade']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioFilterDecadeRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerAudio.addThumbnail(1, thumbnail);

        // Genre
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_by_genre.jpg", description_src: "images/categories/music_by_genre.jpg"});
        thumbnail.setTitles({main: translated_titles['music_by_genre'], thumb: translated_titles['music_by_genre'], history: translated_titles['music_by_genre']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioFilterGenreRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerAudio.addThumbnail(1, thumbnail);        

        // ===
 
        containerList.push(oContainerVideo);
        containerList.push(oContainerAudio);
 
        return containerList;
    }  
}


// ===================
// === Music-Video ===
// ===   Decade    ===

class MusicVideoFilterDecadeRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let refToThis = this;
        let containerList = [];

        // === On Decades ===

        let oContainerDecades = new ObjThumbnailContainer(translated_titles['music_by_decade']);

        // Bands
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_band.jpg", description_src: "images/categories/music_band.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_band'], thumb: translated_titles['music_level_band'], history: translated_titles['music_level_band']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterDecadeOnBandRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerDecades.addThumbnail(1, thumbnail);

        // Records
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_record.jpg", description_src: "images/categories/music_record.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_record'], thumb: translated_titles['music_level_record'], history: translated_titles['music_level_record']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterDecadeOnRecordRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerDecades.addThumbnail(2, thumbnail);        

        containerList.push(oContainerDecades);
 
        return containerList;
    }  
}


// ===   Genre    ===

class MusicVideoFilterGenreRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let refToThis = this;
        let containerList = [];

        // === On Genre ===

        let oContainerGenre = new ObjThumbnailContainer(translated_titles['music_by_genre']);

        // Band
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_band.jpg", description_src: "images/categories/music_band.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_band'], thumb: translated_titles['music_level_band'], history: translated_titles['music_level_band']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterGenreOnBandRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerGenre.addThumbnail(1, thumbnail);

        // Record
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_record.jpg", description_src: "images/categories/music_record.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_record'], thumb: translated_titles['music_level_record'], history: translated_titles['music_level_record']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoFilterGenreOnRecordRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerGenre.addThumbnail(2, thumbnail);      

        // ===

        containerList.push(oContainerGenre);
 
        return containerList;
    } 
}


!!!!!!!!!!!!!!!!!!!111

// === Music-Audio ===
// ===   Decade    ===
   
class MusicAudioFilterDecadeRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let refToThis = this;
        let containerList = [];

        // === On Decades ===

        let oContainerDecades = new ObjThumbnailContainer(translated_titles['music_by_decade']);

        // Bands
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_band.jpg", description_src: "images/categories/music_band.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_band'], thumb: translated_titles['music_level_band'], history: translated_titles['music_level_band']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioFilterDecadeOnBandRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerDecades.addThumbnail(1, thumbnail);

        // Records
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_record.jpg", description_src: "images/categories/music_record.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_record'], thumb: translated_titles['music_level_record'], history: translated_titles['music_level_record']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioFilterDecadeOnRecordRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerDecades.addThumbnail(2, thumbnail);        

        containerList.push(oContainerDecades);
 
        return containerList;
    }  
}


// ===   Genre    ===

class MusicAudioFilterGenreRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let refToThis = this;
        let containerList = [];

        // === On Genre ===

        let oContainerGenre = new ObjThumbnailContainer(translated_titles['music_by_genre']);

        // Band
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_band.jpg", description_src: "images/categories/music_band.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_band'], thumb: translated_titles['music_level_band'], history: translated_titles['music_level_band']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioFilterGenreOnBandRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerGenre.addThumbnail(1, thumbnail);

        // Record
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_record.jpg", description_src: "images/categories/music_record.jpg"});
        thumbnail.setTitles({main: translated_titles['music_level_record'], thumb: translated_titles['music_level_record'], history: translated_titles['music_level_record']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioFilterGenreOnRecordRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerGenre.addThumbnail(2, thumbnail);      

        // ===

        containerList.push(oContainerGenre);
 
        return containerList;
    }  
}



// === Music-Video ===
class MusicVideoFilterDecadeOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_video', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_video', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_video', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_video', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_video', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_video', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicVideoFilterGenreOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_video', level: 'band', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_video', level: 'band', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_video', level: 'band', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_video', level: 'band', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_video', level: 'band', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_video', level: 'band', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_video', level: 'band', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

class MusicVideoFilterDecadeOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicVideoFilterGenreOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_video', playlist:'*', tags: '*', level: 'band', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class AAAAMusicVideoFilterGroupAbcRestGenerator extends  GeneralRestGenerator{

    //
    // TODO: need REST request to select by Name*
    //
    getContainerList(){
        let containerList = [];

        let filter_a    = {category: 'music_video', level: 'band', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_a},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}






// === Music-Audio ===
class MusicAudioFilterDecadeOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicAudioFilterGenreOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_audio', level: 'band', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_audio', level: 'band', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_audio', level: 'band', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_audio', level: 'band', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_audio', level: 'band', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_audio', level: 'band', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_audio', level: 'band', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];playlist

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

class MusicAudioFilterDecadeOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicAudioFilterGenreOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/playlist/{playlist}/tags/{tags}/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

class AAAMusicAudioFilterGroupAbcRestGenerator extends  GeneralRestGenerator{

    //
    // TODO: need REST request to select by Name*
    //

    getContainerList(){
        let containerList = [];

        let filter_a    = {category: 'music_audio', playlist:'*', tags: '*', level: 'band', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_a},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}













//class MusicAudioLevelRestGenerator extends  GeneralRestGenerator{
//
//    getContainerList(){
//        let containerList = [];
//
//        let filter_70s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '70s'};
//        let filter_80s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '80s'};
//        let filter_90s   = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '90s'};
//        let filter_2000s = {category: 'music_audio', level: 'band', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '2000s'};
//
//        let requestList = [
//            {title: "70s",     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
//            {title: "80s",     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
//            {title: "90s",     rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
//            {title: "2000s",   rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
//        ];
//
//        containerList = this.generateContainers(requestList);
//        return containerList;
//   }
//}


// ==============
// Radioplay MENU
// ==============
//
//class RadioplayMenuGenerator extends  IndividualRestGenerator{
class RadioplayMenuGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_radioplay = {category: 'radio_play', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['radioplay'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_radioplay},
        ];        
        
        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ==============
// Audiobook MENU
// ==============
//
class AudiobookMenuGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_audiobook = {category: 'audiobook', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        // TODO: Separate levels and not levels => new request needed
        let requestList = [
            {title: translated_titles['audiobook'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_audiobook},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ==============
// E-book MENU
// ==============
//
class EbookMenuGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_ebook = {category: 'ebook', level: 'menu', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};
        
        let requestList = [
//            {title: translated_titles['ebook'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/ebook/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['ebook'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_ebook},
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

        let filter_dia = {category: 'dia', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: translated_titles['dia'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/dia/genre/*/theme/*/director/*/actor/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['dia'], rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_dia},            
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

        let filter_entertainment = {category: 'entertainment', level: 'menu', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/entertainment/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: this.container_title, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_entertainment},
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

        let filter_knowledge = {category: 'knowledge', level: 'menu', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/knowledge/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: this.container_title, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_knowledge},                        
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


// ==============
// Personal MENU
// ==============
//
class PersonalLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_knowledge = {category: 'personal', level: 'menu', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/level/{level}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_knowledge},                        
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}