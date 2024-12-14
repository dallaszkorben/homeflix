
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
        let refToThis = this;
        let container_list = [];

        for(let request of requestList){
    
            // Build up the request url out of filter
            for (const [key, value] of Object.entries(request['filter'])) {
                request['rq_url'] = request['rq_url'].format(key, value);
            }

            let oContainer = new ObjThumbnailContainer(request["title"]);            
            container_list.push(oContainer);

            // // Asyncronous GET
            // $.getJSON(request['rq_url'], function(request_result, status, xhr){
            //     if( status == 'success'){
            //         for(let index=0; index<request_result.length; index++){
                    
            //             let line = request_result[index];
            //             let play_list = [];
                    
            //             //
            //             // Collects all media which needs to continuous play
            //             //
            //             for(let sub_index=index; sub_index<request_result.length; sub_index++){
            //                 play_list.push(request_result[sub_index]);
            //             }
                    
            //             let thumbnail = refToThis.generateThumbnail(request['filter'], play_list);
                    
            //             oContainer.addThumbnail(line["id"], thumbnail);
            //         }
            //         if(request_result.length == 0){
            //             const index = container_list.findIndex(item => item === oContainer);
            //             if (index !== -1) {
            //                 container_list.splice(index, 1);
            //             }
            //         }
            //     }
            // });


            let request_id = PREFIX_LOCAL_STORAGE + "-" + request["rq_url"].hashCode()
            let saved_request = getLocalStorage(request_id);
            let request_result = undefined;

            if(saved_request == null || !request["rq_static"]){

                // Send REST request
                request_result = RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"]);
                let stringified_result = JSON.stringify(request_result);

                // It saves only if the request is static. If it is for example playlist (last seen ...), it should be generated always generated
                if(request["rq_static"]){
                    setLocalStorage(request_id, stringified_result);
                }

            }else{
                request_result = JSON.parse(saved_request);
            }
            
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

            if(request_result.length == 0){
                const index = container_list.findIndex(item => item === oContainer);
                if (index !== -1) {
                    container_list.splice(index, 1);
                }
            }

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
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/next/mixed/card_id/" + this.hierarchy_id + "/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: this.filters},
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
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_playlists.jpg", description_src: "images/categories/movie_playlists.jpg"});
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
        oContainer.addThumbnail(6, thumbnail);

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
        oContainer.addThumbnail(4, thumbnail);

        // By ABC
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/movie_by_title_abc.jpg", description_src: "images/categories/movie_by_title_abc.jpg"});
        thumbnail.setTitles({main: translated_titles['movie_by_title_abc'], thumb: translated_titles['movie_by_title_abc'], history: translated_titles['movie_by_title_abc']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MovieFilterAbcRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainer.addThumbnail(5, thumbnail);

        // ---

        containerList.push(oContainer);
 
        return containerList;
    }
}


class MovieFilterGenreRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let filter_drama       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'drama',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_scifi       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'scifi',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_fantasy     = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'fantasy',                themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_comedy      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'comedy_AND__NOT_teen',   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_teen        = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'teen',                   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_satire      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'satire',                 themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_crime       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'crime',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_action      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'action',                 themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_thriller    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'thriller',               themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_western     = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'western',                themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_war         = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'war',                    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_music       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'music',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_documentary = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'documentary',            themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_trash       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'trash',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_movie['drama'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_drama},
            {title: translated_genre_movie['scifi'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_scifi},
            {title: translated_genre_movie['fantasy'],     rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_fantasy},
            {title: translated_genre_movie['comedy'],      rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_comedy},
            {title: translated_genre_movie['teen'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_teen},
            {title: translated_genre_movie['satire'],      rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_satire},
            {title: translated_genre_movie['crime'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_crime},
            {title: translated_genre_movie['action'],      rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_action},
            {title: translated_genre_movie['thriller'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_thriller},
            {title: translated_genre_movie['western'],     rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_western},
            {title: translated_genre_movie['war'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_war},
            {title: translated_genre_movie['music'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_music},
            {title: translated_genre_movie['documentary'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_documentary},
            {title: translated_genre_movie['trash'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_trash},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterThemeRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let containerList = [];

        let filter_apocalypse    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'apocalypse', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_dystopia      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'dystopia',   directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_conspiracy    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'conspiracy', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_drog          = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'drog',       directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_maffia        = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'maffia',     directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_broker        = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'broker',     directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_media         = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'media',      directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_evil          = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'evil',       directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_alien         = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'alien',      directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_revenge       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'revenge',    directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_themes['apocalypse'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_apocalypse},
            {title: translated_themes['dystopia'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_dystopia},
            {title: translated_themes['conspiracy'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_conspiracy},
            {title: translated_themes['drog'],             rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_drog},
            {title: translated_themes['maffia'],           rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_maffia},
            {title: translated_themes['broker'],           rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_broker},
            {title: translated_themes['media'],            rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_media},
            {title: translated_themes['evil'],             rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_evil},
            {title: translated_themes['alien'],            rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alien},
            {title: translated_themes['revenge'],          rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_revenge},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterDirectorRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let refToThis = this;

        let containerList = [];
        let requestList = [];

        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/collect/directors/by/movie/count";
        let rq_assync = false;
        let rq_data = {"category": "movie", "minimum": 2, "limit": 40}
        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data })     
    
        let response_dict = response.responseJSON;
        let result = response_dict['result']
        let data_list = response_dict['data']

        // If the query was OK and there was 1 record
        if (result && data_list.length > 0){

            $.each( data_list, function( key, value ) {
                let filter = {
                    category: 'movie',
                    playlist: '*',
                    tags: '*',
                    level: '*',
                    filter_on: '*',
                    title: '*',
                    title: '*',
                    genres:'*',
                    themes: '*',
                    directors: value,
                    actors: '*',
                    lecturers: '*',
                    performers: '*',
                    origins: '*',
                    decade: '*'  
                }
                let line_dict = {
                    title: value,
                    rq_static: true,
                    rq_method: "GET",
                    rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  refToThis.language_code, 
                    filter: filter
                }                
                requestList.push(line_dict);
            });
        }

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterActorRestGenerator extends  GeneralRestGenerator{
    getContainerList(){
        let refToThis = this;

        let containerList = [];
        let requestList = [];

        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/collect/actors/by/role/count";
        let rq_assync = false;
        let rq_data = {"category": "movie", "minimum": 3, "limit": 40}
        let response = $.getJSON({ method: rq_method, url: rq_url, async: rq_assync, dataType: "json", data: rq_data })     
    
        let response_dict = response.responseJSON;
        let result = response_dict['result']
        let data_list = response_dict['data']

        // If the query was OK and there was 1 record
        if (result && data_list.length > 0){

            $.each( data_list, function( key, value ) {
                let filter = {
                    category: 'movie',
                    playlist: '*',
                    tags: '*',
                    level: '*',
                    filter_on: '*',
                    title: '*',
                    title: '*',
                    genres:'*',
                    themes: '*',
                    directors: '*',
                    actors: value,
                    lecturers: '*',
                    performers: '*',
                    origins: '*',
                    decade: '*'  
                }
                let line_dict = {
                    title: value,
                    rq_static: true,
                    rq_method: "GET",
                    rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  refToThis.language_code, 
                    filter: filter
                }                
                requestList.push(line_dict);
            });
        }

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


class MovieFilterAbcRestGenerator extends  GeneralRestGenerator{

    //
    // TODO: need REST request to select by Name*
    //
    getContainerList(){
        let containerList = [];

        let filter_0_9  = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: '0%25_OR_1%25_OR_2%25_OR_3%25_OR_4%25_OR_5%25_OR_6%25_OR_7%25_OR_8%25_OR_9%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_a    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'A%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_b    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'B%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_c    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'C%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_d    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'D%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_e    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'E%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_f    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'F%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_g    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'G%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_h    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'H%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_i    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'I%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_j    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'J%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_k    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'K%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_l    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'L%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_m    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'M%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_n    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'N%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_o    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'O%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_p    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'P%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_q    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'Q%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_r    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'R%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_s    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'S%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_t    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'T%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_u    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'U%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_v    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'V%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_w    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'W%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_x    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'X%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_y    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'Y%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_z    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '-', title: 'Z%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: '0-9',  rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_0_9},
            {title: 'A',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_a},
            {title: 'B',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_b},
            {title: 'C',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_c},
            {title: 'D',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_d},
            {title: 'E',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_e},
            {title: 'F',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_f},
            {title: 'G',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_g},
            {title: 'H',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_h},
            {title: 'I',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_i},
            {title: 'J',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_j},
            {title: 'K',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_k},
            {title: 'L',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_l},
            {title: 'M',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_m},
            {title: 'N',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_n},
            {title: 'O',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_o},
            {title: 'P',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_p},
            {title: 'Q',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_q},
            {title: 'R',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_r},
            {title: 'S',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_s},
            {title: 'T',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_t},
            {title: 'U',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_u},
            {title: 'V',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_v},
            {title: 'W',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_w},
            {title: 'X',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_x},
            {title: 'Y',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_y},
            {title: 'Z',    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_z},
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

        let series_tail_filter         = {category: 'movie', playlist: '*',  tags: '*', level: 'series', filter_on: '*', title: '*', genres:'tale',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let series_comedy_filter       = {category: 'movie', playlist: '*',  tags: '*', level: 'series', filter_on: '*', title: '*', genres:'comedy',      themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let series_drama_filter        = {category: 'movie', playlist: '*',  tags: '*', level: 'series', filter_on: '*', title: '*', genres:'drama',       themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let series_thriller_filter     = {category: 'movie', playlist: '*',  tags: '*', level: 'series', filter_on: '*', title: '*', genres:'thriller',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let series_scifi_filter        = {category: 'movie', playlist: '*',  tags: '*', level: 'series', filter_on: '*', title: '*', genres:'scifi',       themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let series_documentary_filter  = {category: 'movie', playlist: '*',  tags: '*', level: 'series', filter_on: '*', title: '*', genres:'documentary', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        // let series_filter        = {category: 'movie', playlist: '*',  tags: '*', level: 'series', title: '*', genres:'*',      themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title + "-" + translated_genre_movie['tale'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_tail_filter},
            {title: this.container_title + "-" + translated_genre_movie['drama'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_drama_filter},
            {title: this.container_title + "-" + translated_genre_movie['comedy'],      rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_comedy_filter},
            {title: this.container_title + "-" + translated_genre_movie['thriller'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_thriller_filter},           
            {title: this.container_title + "-" + translated_genre_movie['scifi'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_scifi_filter},
            {title: this.container_title + "-" + translated_genre_movie['documentary'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_documentary_filter},

        //    {title: this.container_title + "-", rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: series_filter}
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

        let sequel_drama_filter    = {category: 'movie', playlist: '*',  tags: '*', level: 'sequel', filter_on: '*', title: '*', genres:'drama',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let sequel_comedy_filter   = {category: 'movie', playlist: '*',  tags: '*', level: 'sequel', filter_on: '*', title: '*', genres:'comedy',   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let sequel_thriller_filter = {category: 'movie', playlist: '*',  tags: '*', level: 'sequel', filter_on: '*', title: '*', genres:'thriller', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let sequel_action_filter   = {category: 'movie', playlist: '*',  tags: '*', level: 'sequel', filter_on: '*', title: '*', genres:'action',   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let sequel_scifi_filter    = {category: 'movie', playlist: '*',  tags: '*', level: 'sequel', filter_on: '*', title: '*', genres:'scifi',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        // let sequel_filter = {category: 'movie', playlist: '*',  tags: '*', level: 'sequel', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title + "-" + translated_genre_movie['drama'],     rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_drama_filter},
            {title: this.container_title + "-" + translated_genre_movie['comedy'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_comedy_filter},
            {title: this.container_title + "-" + translated_genre_movie['thriller'],  rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_thriller_filter},
            {title: this.container_title + "-" + translated_genre_movie['action'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_action_filter},
            {title: this.container_title + "-" + translated_genre_movie['scifi'],     rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_scifi_filter},

        //    {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: sequel_filter}
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

        let remake_filter = {category: 'movie', playlist: '*',  tags: '*', level: 'remake', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: remake_filter}
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

        let interrupted_filter =  {category: 'movie', playlist: 'interrupted',  tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let last_watched_filter = {category: 'movie', playlist: 'last_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let most_watched_filter = {category: 'movie', playlist: 'most_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['movie_interrupted'],  rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: interrupted_filter},
            {title: translated_titles['movie_last_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: last_watched_filter},
            {title: translated_titles['movie_most_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: most_watched_filter}
        ];

        // Get the existion TAGs
        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/personal/tag/get";
        let rq_data = {"category": "movie"};
        let rq_assync = false;
        let response = $.getJSON({ method: rq_method, url: rq_url, data: rq_data, async: rq_assync});
        if(response.status == 200 && response.responseJSON["result"]){
            for (let data_dict of response.responseJSON["data"]){
                let filter = {category: 'movie', playlist: '*', tags: data_dict["name"], level: '*', title: '*', genres: '*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', origins: '*', decade: '*'};
                let request = {title: data_dict["name"], rq_static: false, rq_method: 'GET', rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter};
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
        oContainerVideo.addThumbnail(2, thumbnail);        

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
        oContainerVideo.addThumbnail(3, thumbnail);
        
        // Playlist
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_video_playlists.jpg", description_src: "images/categories/music_video_playlists.jpg"});
        thumbnail.setTitles({main: translated_titles['music_video_playlists'], thumb: translated_titles['music_video_playlists'], history: translated_titles['music_video_playlists']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicVideoPlaylistsRestGenerator(refToThis.language_code, translated_titles['music_video_playlists']);
                            };
                        })("music_video")
                },
            "continuous": []
        });
        oContainerVideo.addThumbnail(4, thumbnail);


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
        oContainerAudio.addThumbnail(2, thumbnail);

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
                                return new MusicAudioFilterGroupAbcRestGenerator(refToThis.language_code);
                            };
                        })("blabla")
                },
            "continuous": []
        });
        oContainerAudio.addThumbnail(3, thumbnail);

        // Playlist
        thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/music_audio_playlists.jpg", description_src: "images/categories/music_audio_playlists.jpg"});
        thumbnail.setTitles({main: translated_titles['music_audio_playlists'], thumb: translated_titles['music_audio_playlists'], history: translated_titles['music_audio_playlists']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(movie_type) {
                            return function() {
                                return new MusicAudioPlaylistsRestGenerator(refToThis.language_code, translated_titles['music_audio_playlists']);
                            };
                        })("music_video")
                },
            "continuous": []
        });
        oContainerAudio.addThumbnail(4, thumbnail);

        // ===
 
        containerList.push(oContainerVideo);
        containerList.push(oContainerAudio);
 
        return containerList;
    }  
}


// ===================
// === Music-Video ===
// ===================

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


// === ABC ===
class MusicVideoFilterGroupAbcRestGenerator extends  GeneralRestGenerator{

    //
    // TODO: need REST request to select by Name*
    //
    getContainerList(){
        let containerList = [];

        let filter_a    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'A%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_b    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'B%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_c    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'C%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_d    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'D%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_e    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'E%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_f    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'F%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_g    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'G%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_h    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'H%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_i    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'I%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_j    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'J%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_k    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'K%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_l    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'L%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_m    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'M%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_n    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'N%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_o    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'O%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_p    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'P%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_q    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'Q%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_r    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'R%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_s    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'S%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_t    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'T%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_u    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'U%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_v    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'V%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_w    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'W%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_x    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'X%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_y    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'Y%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_z    = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'Z%25', genres:'*',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: 'A', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_a},
            {title: 'B', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_b},
            {title: 'C', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_c},
            {title: 'D', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_d},
            {title: 'E', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_e},
            {title: 'F', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_f},
            {title: 'G', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_g},
            {title: 'H', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_h},
            {title: 'I', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_i},
            {title: 'J', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_j},
            {title: 'K', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_k},
            {title: 'L', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_l},
            {title: 'M', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_m},
            {title: 'N', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_n},
            {title: 'O', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_o},
            {title: 'P', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_p},
            {title: 'Q', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_q},
            {title: 'R', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_r},
            {title: 'S', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_s},
            {title: 'T', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_t},
            {title: 'U', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_u},
            {title: 'V', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_v},
            {title: 'W', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_w},
            {title: 'X', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_x},
            {title: 'Y', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_y},
            {title: 'Z', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_z},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}



// ===   Playlist    ===

class MusicVideoPlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        //let interrupted_filter =  {category: 'music_video', playlist: 'interrupted',  tags: '*', level: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let last_watched_filter = {category: 'music_video', playlist: 'last_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let most_watched_filter = {category: 'music_video', playlist: 'most_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['music_video_last_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: last_watched_filter},
            {title: translated_titles['music_video_most_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: most_watched_filter}
        ];


        // Get the existion TAGs
        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/personal/tag/get";
        let rq_data = {"category": "music_video"};
        let rq_assync = false;
        let response = $.getJSON({ method: rq_method, url: rq_url, data: rq_data, async: rq_assync});
        if(response.status == 200 && response.responseJSON["result"]){
            for (let data_dict of response.responseJSON["data"]){
                let filter = {category: 'music_video', playlist: '*', tags: data_dict["name"], level: '*', title: '*', genres: '*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', origins: '*', decade: '*'};
                let request = {title: data_dict["name"], rq_static: false, rq_method: 'GET', rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter};
                requestList.push(request);
            }
        }

        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// ===================
// === Music-Audio ===
// ===================

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

// === ABC ===
class MusicAudioFilterGroupAbcRestGenerator extends  GeneralRestGenerator{

    //
    // TODO: need REST request to select by Name*
    //
    getContainerList(){
        let containerList = [];

        let filter_0_9 = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '0%25_OR_1%25_OR_2%25_OR_3%25_OR_4%25_OR_5%25_OR_6%25_OR_7%25_OR_8%25_OR_9%25_OR_9%25', origins: '*', decade: '*'};
        let filter_a   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'A%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_b   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'B%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_c   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'C%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_d   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'D%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_e   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'E%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_f   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'F%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_g   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'G%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_h   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'H%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_i   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'I%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_j   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'J%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_k   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'K%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_l   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'L%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_m   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'M%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_n   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'N%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_o   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'O%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_p   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'P%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_q   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'Q%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_r   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'R%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_s   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'S%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_t   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'T%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_u   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'U%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_v   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'V%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_w   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'W%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_x   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'X%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_y   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'Y%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};
        let filter_z   = {category: 'music_audio', playlist: '*',  tags: '*', level: 'band', filter_on: '-', title: 'Z%25', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*',                                                                                 origins: '*', decade: '*'};


        let requestList = [
            {title: '0-9', rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_0_9},
            {title: 'A',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_a},
            {title: 'B',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_b},
            {title: 'C',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_c},
            {title: 'D',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_d},
            {title: 'E',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_e},
            {title: 'F',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_f},
            {title: 'G',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_g},
            {title: 'H',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_h},
            {title: 'I',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_i},
            {title: 'J',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_j},
            {title: 'K',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_k},
            {title: 'L',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_l},
            {title: 'M',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_m},
            {title: 'N',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_n},
            {title: 'O',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_o},
            {title: 'P',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_p},
            {title: 'Q',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_q},
            {title: 'R',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_r},
            {title: 'S',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_s},
            {title: 'T',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_t},
            {title: 'U',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_u},
            {title: 'V',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_v},
            {title: 'W',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_w},
            {title: 'X',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_x},
            {title: 'Y',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_y},
            {title: 'Z',   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_z},
        ];
        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

// ===   Playlist    ===

class MusicAudioPlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let last_watched_filter = {category: 'music_audio', playlist: 'last_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let most_watched_filter = {category: 'music_audio', playlist: 'most_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['music_audio_last_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: last_watched_filter},
            {title: translated_titles['music_audio_most_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: most_watched_filter}
        ];

        // Get the existion TAGs
        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/personal/tag/get";
        let rq_data = {"category": "music_audio"};
        let rq_assync = false;
        let response = $.getJSON({ method: rq_method, url: rq_url, data: rq_data, async: rq_assync});
        if(response.status == 200 && response.responseJSON["result"]){
            for (let data_dict of response.responseJSON["data"]){
                let filter = {category: 'music_audio', playlist: '*', tags: data_dict["name"], level: '*', title: '*', genres: '*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', origins: '*', decade: '*'};
                let request = {title: data_dict["name"], rq_static: false, rq_method: 'GET', rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter};
                requestList.push(request);
            }
        }
        containerList = this.generateContainers(requestList);
        return containerList;
    }
}


// === Music-Video ===
class MusicVideoFilterDecadeOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_video', playlist: '*',  tags: '*', level: 'band', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicVideoFilterGenreOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_video', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

class MusicVideoFilterDecadeOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicVideoFilterGenreOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_video', playlist:'*', tags: '*', level: '*', title: '*', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}









// === Music-Audio ===
class MusicAudioFilterDecadeOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicAudioFilterGenreOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_audio', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}

class MusicAudioFilterDecadeOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_60s   = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '60s'};
        let filter_70s   = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '70s'};
        let filter_80s   = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '80s'};
        let filter_90s   = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '90s'};
        let filter_2000s = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2000s'};
        let filter_2010s = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '2010s'};

        let requestList = [
            {title: "60s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_60s},
            {title: "70s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_70s},
            {title: "80s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_80s},
            {title: "90s",   rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_90s},
            {title: "2000s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2000s},
            {title: "2010s", rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_2010s},
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}


class MusicAudioFilterGenreOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(){
        let containerList = [];

        let filter_new_wave    = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'new_wave',    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_electronic  = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'electronic',  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_pop         = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'pop',         themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_synth       = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'synth',       themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_rorck       = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'rock',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_alternative = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'alternative', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_punk        = {category: 'music_audio', playlist:'*', tags: '*', level: '*', title: '*', genres:'punk',        themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_genre_music['new_wave'],    rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_new_wave},
            {title: translated_genre_music['electronic'],  rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_electronic},
            {title: translated_genre_music['pop'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_pop},
            {title: translated_genre_music['synth'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_synth},
            {title: translated_genre_music['rock'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_rorck},
            {title: translated_genre_music['alternative'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alternative},
            {title: translated_genre_music['punk'],        rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_punk},
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

        let filter_radioplay = {category: 'radio_play', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['radioplay'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_radioplay},
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
        let refToThis = this;
        let containerList = [];

        let filter_audiobook = {category: 'audiobook', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        // TODO: Separate levels and not levels => new request needed
        let requestList = [
            {title: translated_titles['audiobook'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_audiobook},
        ];

        containerList = this.generateContainers(requestList);

        // Playlist
        let oContainer = new ObjThumbnailContainer(translated_titles['audiobook']);
        let thumbnail = new Thumbnail();
        thumbnail.setImageSources({thumbnail_src: "images/categories/audiobook_playlists.jpg", description_src: "images/categories/audiobook_playlists.jpg"});
        thumbnail.setTitles({main: translated_titles['audiobook_playlists'], thumb: translated_titles['audiobook_playlists'], history: translated_titles['audiobook_playlists']});
        thumbnail.setFunctionForSelection({
            "single": 
                {
                    "menu": 
                        (function(music_type) {
                            return function() {
                                return new AudiobookPlaylistsRestGenerator(refToThis.language_code, translated_titles['audiobook_playlists']);
                            };
                        })("music_video")
                },
            "continuous": []
        });
        oContainer.addThumbnail(1, thumbnail);
        containerList.push(oContainer);
 
        return containerList;
    }
}

class AudiobookPlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(){
        let containerList = [];

        let interrupted_filter =  {category: 'audiobook', playlist: 'interrupted',  tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let last_watched_filter = {category: 'audiobook', playlist: 'last_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let most_watched_filter = {category: 'audiobook', playlist: 'most_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['audiobook_interrupted'],  rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: interrupted_filter},
            {title: translated_titles['audiobook_last_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: last_watched_filter},
            {title: translated_titles['audiobook_most_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: most_watched_filter}
        ];


        // Get the existion TAGs
        let rq_method = "GET";
        let rq_url = "http://" + host + port + "/personal/tag/get";
        let rq_data = {"category": "audiobook"};
        let rq_assync = false;
        let response = $.getJSON({ method: rq_method, url: rq_url, data: rq_data, async: rq_assync});
        if(response.status == 200 && response.responseJSON["result"]){
            for (let data_dict of response.responseJSON["data"]){
                let filter = {category: 'audiobook', playlist: '*', tags: data_dict["name"], level: '*', title: '*', genres: '*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', origins: '*', decade: '*'};
                let request = {title: data_dict["name"], rq_static: false, rq_method: 'GET', rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter};
                requestList.push(request);
            }
        }
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

        let filter_ebook = {category: 'ebook', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        
        let requestList = [
//            {title: translated_titles['ebook'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/ebook/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['ebook'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_ebook},
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

        let filter_dia = {category: 'dia', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: translated_titles['dia'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/dia/genre/*/theme/*/director/*/actor/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['dia'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_dia},            
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

        let filter_entertainment = {category: 'entertainment', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/entertainment/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_entertainment},
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

        let filter_knowledge = {category: 'knowledge', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/knowledge/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_knowledge},                        
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

        let filter_knowledge = {category: 'personal', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_knowledge},                        
        ];

        containerList = this.generateContainers(requestList);
        return containerList;
   }
}