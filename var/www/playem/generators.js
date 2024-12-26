
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

    isThumbnailShowSynchronous(){
        return false;
    }

    showContainers(objScrollSection){
        let refToThis = this
        Generator.startSpinner();

        // Force GUI refresh to make the spinner visible
        setTimeout(function () {

            let containerList;

            if(refToThis.isThumbnailShowSynchronous()){
                containerList = refToThis.getContainerList();
            }else{
                containerList = refToThis.getContainerList(
                    function(){
                        Generator.stopSpinner();
                        objScrollSection.focusDefault();
                        objScrollSection.buildUpDom()
                    },
                    function(){
                        //Generator.stopSpinner();
                        //objScrollSection.focusDefault();
                        objScrollSection.buildUpDom()
                    }
                );
            }

            containerList.forEach(oContainer => {
                objScrollSection.addThumbnailContainerObject(oContainer);
                }
            );

            if(refToThis.isThumbnailShowSynchronous()){
                Generator.stopSpinner();
                objScrollSection.focusDefault();
            }

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

    static sendRestRequest(rq_method, rq_url, rq_data){
        let rq_assync = false;
        let result;

        if( rq_data !== null && rq_data !== undefined){
            result = $.getJSON({method: rq_method, url: rq_url, data: rq_data, async: rq_assync, dataType: "json"});
        }else{
            result = $.getJSON({method: rq_method, url: rq_url, async: rq_assync, dataType: "json"});
        }
        return result.responseJSON;
    }

    generateThumbnail(data_dict, play_list){
        throw new Error("Implement generateThumbnails() method in the " + this.constructor.name + " class!");
    }

    getTruncatedTitle(text, max_length){
        let tail = "...";
        if (text.length > max_length + tail.length)
            text = text.slice(0, max_length) + tail;
        return text;
    }


    /**
     *
     * TODO:
     *
     * make the containers generation faster:
     * - read the next element
     * - if it is empty, skip and get the next element
     * - if it is not empty, in an async function show it
     *
     */
    async FixIt_generateContainers(requestList, callBackMinimalThumbnails, callBackAllThumbnails){
        let refToThis = this;
        let container_list = [];
        let response_list = [];
        let processingPromises = []; // To track all async operations

        for(let request of requestList){
            let thumbnail_list = RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"], request["rq_data"]);

            if(thumbnail_list.length > 0){
                let oContainer = new ObjThumbnailContainer(request["title"]);
                container_list.push(oContainer);

                async function processContainer(rq_data, oContainer, thumbnail_list) {

//                    // Waiting needed to be sure the function will return before the 'minimalThumbnails() callback function returns
                    await delay(100);

                    for(let thumbnail_index = 0; thumbnail_index < thumbnail_list.length; thumbnail_index++){

                        let thumbnail_dict = thumbnail_list[thumbnail_index];
                        let play_list = [];

                        for (let sub_index = thumbnail_index; sub_index < thumbnail_list.length; sub_index++) {
                            play_list.push(thumbnail_list[sub_index]);
                        }

                        // request["rq_data"] needed by parameter
                        let thumbnail = refToThis.generateThumbnail(rq_data, play_list);
                        oContainer.addThumbnail(thumbnail_dict["id"], thumbnail);
                    }
                }

                const processPromise = processContainer(
                    request["rq_data"],
                    oContainer,
                    thumbnail_list
                );

                // Start the processing
                await processContainer(request["rq_data"], oContainer, thumbnail_list);

            }

        }

        return container_list;
    }

    generateContainers(requestList, minimalThumbnails, allThumbnails){
        let refToThis = this;
        let container_list = [];
        let response_list = [];

        for(let request of requestList){

            //
            // Syncronous GET / Async fill up
            //

            // === Caching Strategy for REST Responses ===
            // We use LocalStorage to cache REST responses and avoid redundant server requests.
            // A new REST request is only made when either:
            // 1. It's the first time accessing this data
            // 2. The data is dynamic (!request["rq_static"])
            //
            // Note: On WebOS, performance bottleneck remains due to slow thumbnail rendering, rather than REST request latency.
            // :(
            let request_id = PREFIX_LOCAL_STORAGE + "-" + request["rq_url"].hashCode() + "-" + JSON.stringify(request["rq_data"]).hashCode()
//            let saved_request = getLocalStorage(request_id);
            let request_result = undefined;

//            if(saved_request === null || saved_request === undefined || !request["rq_static"]){

                // Send REST request
                request_result = RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"], request["rq_data"]);
                let stringified_result = JSON.stringify(request_result);

                // It saves only if the request is static. If it is for example playlist (last seen ...), it should be generated always generated
                if(request["rq_static"]){
                    setLocalStorage(request_id, stringified_result);
                }

//            }else{
//                request_result = JSON.parse(saved_request);
//            }

            // Now I have the request_result for the recent thumbnail container
            // Add this container to the container list if it is possible and needed
            // Add the thumbnail line if the content is not empty or the request is not static. If the request is dynamic, then the empty result can be different later
//            if(request_result.length > 0 || !request['rq_static']){
            if(request_result.length > 0){

                let oContainer = new ObjThumbnailContainer(request["title"]);
                container_list.push(oContainer);

                // Add the result to a dictionary to a later process after this loop
                response_list.push({data_dict: request['rq_data'], container: oContainer, result: request_result})

            }
        }

        // Now every response are collected in 'response_dict'

        // === Thumbnail load section ===
        async function processContainers() {

            // Waiting needed to be sure the function will return before the 'minimalThumbnails() callback function returns
            await delay(100);

            // Phase 1: Synchronous generation of initial thumbnails
            const MAX_LINES = 3;       // Maximum number of lines to process initially
            const MAX_THUMBNAILS = 11; // Maximum number of thumbnails per line initially

            const actualLines = Math.min(response_list.length, MAX_LINES);
            for (let lineIndex = 0; lineIndex < actualLines; lineIndex++) {
                const response = response_list[lineIndex];
                const actualThumbnails = Math.min(response['result'].length, MAX_THUMBNAILS);

                for (let index = 0; index < actualThumbnails; index++) {
                    let line = response['result'][index];
                    let play_list = [];

                    for (let sub_index = index; sub_index < response['result'].length; sub_index++) {
                        play_list.push(response['result'][sub_index]);
                    }

                    let thumbnail = refToThis.generateThumbnail(response['data_dict'], play_list);
                    response['container'].addThumbnail(line["id"], thumbnail);
                }
            }

            // Initial batch is done, call the callback
            minimalThumbnails();
            await delay(100);

            // Phase 2: Asynchronous generation of remaining thumbnails
            const linePromises = response_list.map((response, lineIndex) => {
                return new Promise(async (resolve) => {

                    // For lines we already processed partially
                    if (lineIndex < MAX_LINES) {

                        // Continue from where we left off
                        for (let index = MAX_THUMBNAILS; index < response['result'].length; index++) {
                            await delay(1);

                            let line = response['result'][index];
                            let play_list = [];

                            for (let sub_index = index; sub_index < response['result'].length; sub_index++) {
                                play_list.push(response['result'][sub_index]);
                            }

                            let thumbnail = refToThis.generateThumbnail(response['data_dict'], play_list);
                            response['container'].addThumbnail(line["id"], thumbnail);
                        }
                    }

                    // For lines we haven't processed at all
                    else {
                        for (let index = 0; index < response['result'].length; index++) {
                            await delay(1);
                            let line = response['result'][index];
                            let play_list = [];

                            for (let sub_index = index; sub_index < response['result'].length; sub_index++) {
                                play_list.push(response['result'][sub_index]);
                            }

                            let thumbnail = refToThis.generateThumbnail(response['data_dict'], play_list);
                            response['container'].addThumbnail(line["id"], thumbnail);
                        }
                    }
                    resolve();
                });
            });

            try {
                // Wait for all remaining thumbnails to complete
                await Promise.all(linePromises);
                allThumbnails();
            } catch (error) {
                console.error('Error processing containers:', error);
            }
        }

        // Start the processing
        processContainers();

        // It is time to return the container list with yet empty thumbnail containers
        // The caller will add the containers to the scroll section
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

    generateThumbnail(data_dict, play_list){
        let hit = play_list[0];

        let refToThis = this;
        let thumbnail = new Thumbnail();

        let thumbnail_title = this.getThumbnailTitle(hit);
        let history_title = this.getHistoryTitle(hit);
        let main_title = RestGenerator.getMainTitle(hit);

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
                            (function(hierarchy_id, data_dict) {
                                return function() {
                                    return new SubLevelRestGenerator(refToThis.language_code, history_title, hierarchy_id, data_dict);
                                };
                            })(hit["id"], data_dict )
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
    constructor(language_code, container_title, hierarchy_id, data_dict){
        super(language_code);
        this.container_title = container_title;
        this.hierarchy_id = hierarchy_id;
        this.data_dict = data_dict;
    }

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        this.data_dict['card_id'] = this.hierarchy_id;
        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/next/mixed/card_id/" + this.hierarchy_id + "/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: this.filters},
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/next/mixed", rq_data: this.data_dict},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}














function generateMenu(menuDict){
    let ext = menuDict.extends ?? null;
    let isThumbnailShowSynchronous = menuDict.is_thumbnail_show_synchronous ?? false;
    let retClass;

    if (ext === 'Generator' || ext == 'GeneralRestGenerator') {
        let getContainerListBody = `
                        let refToThis = _this;
                        let containerList = [];
                        let requestList = [];
                        let request;
                        let translator;
                        let title;
        `;
        let isRequest = false;

        let containerList = menuDict.container_list ?? [];
        for (let containerDict of containerList) {
            let descriptorStaticHardCodedDict = containerDict.static_hard_coded ?? null;
            let descriptorDynamicHardCodedDict = containerDict.dynamic_hard_coded ?? null;
            let descriptorDynamicQueried = containerDict.dynamic_queried ?? null;
            let order = containerDict.order ?? 0

            // Static - Hard Coded Container Definitions
            if(descriptorStaticHardCodedDict !== null){

                let container_title_keycontainerTitleKey = descriptorStaticHardCodedDict.container_title_key ?? "unknown";
                getContainerListBody += `
                        let oContainer${order} = new ObjThumbnailContainer(translated_titles['${container_title_keycontainerTitleKey}']);
                        let thumbnail;
                `;

                let thumbnailList = descriptorStaticHardCodedDict.thumbnails ?? [];
                for (let thumbnailDict of thumbnailList){

                    let thumbnailOrder = thumbnailDict.order ?? "";
                    let thumbnailImage = thumbnailDict.thumbnail.image ?? "";
                    let thumbnailtitleKey = thumbnailDict.thumbnail.title_key ?? "";
                    let descriptionImage = thumbnailDict.description.image ?? "";
                    let descriptiontitleKey = thumbnailDict.description.title_key ?? "";
                    let historytitleKey = thumbnailDict.history.title_key ?? "";
                    let menuDict = thumbnailDict.execution ?? {};
                    let menuDictString = JSON.stringify(menuDict);

                    getContainerListBody += `
                        thumbnail = new Thumbnail();
                        thumbnail.setImageSources({thumbnail_src: "${thumbnailImage}", description_src: "${descriptionImage}"});
                        thumbnail.setTitles({main: translated_titles["${thumbnailtitleKey}"], thumb: translated_titles["${descriptiontitleKey}"], history: translated_titles["${historytitleKey}"]});
                        thumbnail.setFunctionForSelection({
                            "single":
                                {
                                    "menu": ( function(movie_type) {
                                                return function() {
                                                    let menuClass = generateMenu(${menuDictString});
                                                    let menu = new menuClass(refToThis.language_code);
                                                    return menu;
                                                };
                                            })("for_later_use")
                                },
                            "continuous": []
                        });
                        oContainer${order}.addThumbnail(${thumbnailOrder}, thumbnail);
                `
                }

                getContainerListBody += `
                        containerList.push(oContainer${order});
                `

            // Dynamic - Hard Coded Container Definitions
            }else if(descriptorDynamicHardCodedDict !== null){

                let translator = descriptorDynamicHardCodedDict.title.dict_translator ?? null;
                let title = descriptorDynamicHardCodedDict.title.key ?? "unknown";
                let data = descriptorDynamicHardCodedDict.data ?? {};
                let request = descriptorDynamicHardCodedDict.request ?? {static: true, method: "GET", protocol: "http", url: ""}
                let rq_static = request.static
                let rq_method = request.method
                let rq_protocol = request.protocol
                let rq_path = request.path

                let rq_data = `{`;
                for( const[key, value] of Object.entries(data)){
                    rq_data += `${key}: "${value}", `
                }
                rq_data += `lang: refToThis.language_code}`

                title = (translator !== null) ? `${translator}["${title}"]` : `"${title}"`;

                getContainerListBody += `
                        request = {title: ${title}, rq_static:${rq_static}, rq_method: "${rq_method}", rq_url: "${rq_protocol}://" + host + port + "${rq_path}", rq_data: ${rq_data}};
                        requestList.push(request);
                `
                isRequest = true;

            // Dynamic - Queried Container Definitions
            }else if(descriptorDynamicQueried !== null){

                let pre_query_dict = descriptorDynamicQueried.pre_query ?? {};
                let pre_query_data_dict = pre_query_dict.data ?? {};
                let pre_query_request_dict = pre_query_dict.request ?? {};
                let pre_rq_satic = pre_query_request_dict.static ?? true;
                let pre_rq_method = pre_query_request_dict.method ?? "GET";
                let pre_rq_protocol = pre_query_request_dict.protocol ?? "http";
                let pre_rq_path = pre_query_request_dict.path ?? "";
                let pre_rq_assync = false;
                let query_loop_dict = descriptorDynamicQueried.query_loop ?? {};
                let query_data_dict = query_loop_dict.data ?? {};

                let query_data_dict_map_dict = null;
                let query_data_list_map_value = null;
                let data_from_pre_response_list_dict = query_loop_dict.data_from_pre_response_list ?? {};
                let data_from_pre_response_list_type = data_from_pre_response_list_dict.type ?? "value";
                if(data_from_pre_response_list_type === 'dict'){
                    query_data_dict_map_dict = data_from_pre_response_list_dict.dict ?? null;
                }else if(data_from_pre_response_list_type === 'value'){
                    query_data_list_map_value = data_from_pre_response_list_dict.value;
                }

                let query_request_dict = query_loop_dict.request ?? {};
                let rq_static = query_request_dict.static ?? false;
                let rq_method = query_request_dict.method ?? "GET";
                let rq_protocol = query_request_dict.protocol ?? "http";
                let rq_path = query_request_dict.path ?? "";
                let query_title_dict = query_loop_dict.title ?? {};
                let query_title_dict_translator = query_title_dict.dict_translator ?? null;
                let query_title_key = query_title_dict.key ?? "unknown";

                let pre_rq_data = `{`;
                for( const[key, value] of Object.entries(pre_query_data_dict)){
                    pre_rq_data += `${key}: "${value}", `
                }
                // It was not asked but I add the language anyway.
                pre_rq_data += `lang: refToThis.language_code}`

                let rq_data = `{`;
                for( const[key, value] of Object.entries(query_data_dict)){
                    rq_data += `${key}: "${value}", `
                }
                if(query_data_dict_map_dict !== null){
                    for( const[key, value] of Object.entries(query_data_dict_map_dict)){
                        rq_data += `${key}: data_dict["${value}"], `
                    }
                }else if(query_data_list_map_value !== null){
                    rq_data += `${query_data_list_map_value}: data_value, `
                }
                // It was not asked but I add the language anyway.
                rq_data += `lang: refToThis.language_code}`

                getContainerListBody += `
                        let response = $.getJSON({ method: "${pre_rq_method}", url: "${pre_rq_protocol}://" + host + port + "${pre_rq_path}", data: ${pre_rq_data}, async: ${pre_rq_assync}});
                        if(response.status == 200 && response.responseJSON["result"]){`


                //title = (query_title_dict_translator !== null) ? `${query_title_dict_translator}["${title}"]` : `"${query_title_dict_translator}"`;
                //title = (translator !== null) ? `${translator}["${title}"]` : `"${title}"`;

                // In case of DICT list response from the pre-request
                if(query_data_dict_map_dict !== null){

                    let title = (query_title_dict_translator !== null) ? `${query_title_dict_translator}[data_dict["${query_title_key}"]]` : `data_dict["${query_title_key}"]`;

                    getContainerListBody += `
                            for (let data_dict of response.responseJSON["data"]){
                                let request = {title: ${title}, rq_static: ${rq_static}, rq_method: "${rq_method}", rq_url: "${rq_protocol}://" + host + port + "${rq_path}", rq_data: ${rq_data}};
                                requestList.push(request);
                            }
                        }`
                    isRequest = true;

                // In case of VALUE list response from the pre-request
                }else if(query_data_list_map_value !== null){

                    let title = (query_title_dict_translator !== null) ? `${query_title_dict_translator}[data_value]` : `data_value`;

                    getContainerListBody += `
                            for (let data_value of response.responseJSON["data"]){
                                let request = {title: ${title}, rq_static: ${rq_static}, rq_method: "${rq_method}", rq_url: "${rq_protocol}://" + host + port + "${rq_path}", rq_data: ${rq_data}};
                                requestList.push(request);
                            }
                        }`
                    isRequest = true;
                }
            }
        }

        if(isRequest){
            getContainerListBody += `
                        containerList = refToThis.generateContainers(requestList, minimalThumbnails, allThumbnails);
            `;
        }

        getContainerListBody += `
                        return containerList;
        `;

//        console.log(`                   getContinerList(minimalThumbnails, allThumbnails){\n` + getContainerListBody + `\n                   }`);

        retClass = class extends eval(ext) {
            isThumbnailShowSynchronous() {
                return (new Function('_this', `return ${isThumbnailShowSynchronous};`))(this);
            }

            // If getContainerList has multiple parameters
            // getContainerList(param1, param2) {
            // return (new Function('param1', 'param2', getContainerListBody))(param1, param2);}
            getContainerList(minimalThumbnails, allThumbnails) {

               return (new Function('_this', 'minimalThumbnails', 'allThumbnails', `
                    ${getContainerListBody}`))(this, minimalThumbnails, allThumbnails);
            }
        }

    }else{
        retClass = class extends Generator {
            getContainerList() {
                return [];
            }
        }
    }

    return retClass;
}




// =============================================================================

// =========
// MAIN MENU
// =========
//
class MainMenuGenerator extends Generator{
    isThumbnailShowSynchronous(){
        return true;
    }

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
    isThumbnailShowSynchronous(){
        return true;
    }

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
    isThumbnailShowSynchronous(){
        return true;
    }

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
    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_drama       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'drama_AND__NOT_comedy_AND__NOT_war_AND__NOT_satire_AND__NOT_crime_AND__NOT_thriller_AND__NOT_fantasy_AND__NOT_music_AND__NOT_scifi_AND__NOT_horror',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_scifi       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'scifi_AND__NOT_trash',   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_fantasy     = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'fantasy',                themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_comedy      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'comedy_AND__NOT_teen',   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_teen        = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'teen',                   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_satire      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'satire',                 themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_crime       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'crime_AND__NOT_trash',   themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_action      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'action_AND__NOT_trash',  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_thriller    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'thriller',               themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_horror      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'horror_AND__NOT_trash',  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_western     = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'western',                themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_war         = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'war',                    themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_music       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'music',                  themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_history     = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'history',                themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
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
            {title: translated_genre_movie['horror'],      rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_horror},
            {title: translated_genre_movie['western'],     rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_western},
            {title: translated_genre_movie['war'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_war},
            {title: translated_genre_movie['music'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_music},
            {title: translated_genre_movie['history'],     rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_history},
            {title: translated_genre_movie['documentary'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_documentary},
            {title: translated_genre_movie['trash'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_trash},
        ];

//            let requestList = [ {title: translated_genre_movie['drama'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed", rq_data: {category: 'movie', genres:'scifi', lang: this.language_code}, filter: {}} ];



        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


class MovieFilterThemeRestGenerator extends  GeneralRestGenerator{
    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_apocalypse    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'apocalypse',  directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_dystopia      = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'dystopia',    directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_conspiracy    = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'conspiracy',  directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_drog          = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'drog',        directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_maffia        = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'maffia',      directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_broker        = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'broker',      directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_media         = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'media',       directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_psychopathy   = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'psychopathy', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_evil          = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'evil',        directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_alien         = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'alien',       directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let filter_revenge       = {category: 'movie', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: 'revenge',     directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_themes['apocalypse'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_apocalypse},
            {title: translated_themes['dystopia'],         rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_dystopia},
            {title: translated_themes['conspiracy'],       rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_conspiracy},
            {title: translated_themes['drog'],             rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_drog},
            {title: translated_themes['maffia'],           rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_maffia},
            {title: translated_themes['broker'],           rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_broker},
            {title: translated_themes['media'],            rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_media},
            {title: translated_themes['psychopathy'],      rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_psychopathy},
            {title: translated_themes['evil'],             rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_evil},
            {title: translated_themes['alien'],            rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_alien},
            {title: translated_themes['revenge'],          rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_revenge},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


class MovieFilterDirectorRestGenerator extends  GeneralRestGenerator{
    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


class MovieFilterActorRestGenerator extends  GeneralRestGenerator{
    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


class MovieFilterAbcRestGenerator extends  GeneralRestGenerator{

    //
    // TODO: need REST request to select by Name*
    //
    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}




class MovieSerialsLevelRestGenerator extends  GeneralRestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}



class MovieSequelsLevelRestGenerator extends  GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}

class MovieRemakesLevelRestGenerator extends GeneralRestGenerator{
    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let remake_filter = {category: 'movie', playlist: '*',  tags: '*', level: 'remake', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: remake_filter}
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}




class MoviePlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let interrupted_filter =  {category: 'movie', playlist: 'interrupted',  tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let last_watched_filter = {category: 'movie', playlist: 'last_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};
        let most_watched_filter = {category: 'movie', playlist: 'most_watched', tags: '*', level: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['movie_interrupted'],  rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: interrupted_filter},
            {title: translated_titles['movie_last_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: last_watched_filter},
            {title: translated_titles['movie_most_watched'], rq_static: false, rq_method: "GET", rq_url: "http://" + host + port + "/collect/lowest/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: most_watched_filter}
        ];

        // Get the existing TAGs
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
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
    isThumbnailShowSynchronous(){
        return true;
    }

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
    isThumbnailShowSynchronous(){
        return true;
    }

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
    isThumbnailShowSynchronous(){
        return true;
    }

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
    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}



// ===   Playlist    ===

class MusicVideoPlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


// ===================
// === Music-Audio ===
// ===================

// ===   Decade    ===

class MusicAudioFilterDecadeRestGenerator extends  GeneralRestGenerator{
    isThumbnailShowSynchronous(){
        return true;
    }

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
    isThumbnailShowSynchronous(){
        return true;
    }

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
    getContainerList(minimalThumbnails, allThumbnails){
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
        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}

// ===   Playlist    ===

class MusicAudioPlaylistsRestGenerator  extends GeneralRestGenerator{

    constructor(language_code, container_title){
        super(language_code);
        this.container_title = container_title;
    }

    getContainerList(minimalThumbnails, allThumbnails){
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
        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


// === Music-Video ===
class MusicVideoFilterDecadeOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}


class MusicVideoFilterGenreOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}

class MusicVideoFilterDecadeOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}


class MusicVideoFilterGenreOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}









// === Music-Audio ===
class MusicAudioFilterDecadeOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}


class MusicAudioFilterGenreOnBandRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}

class MusicAudioFilterDecadeOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}


class MusicAudioFilterGenreOnRecordRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
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

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}



// ==============
// Radioplay MENU
// ==============
//
//class RadioplayMenuGenerator extends  IndividualRestGenerator{
class RadioplayMenuGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_radioplay = {category: 'radio_play', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: translated_titles['radioplay'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_radioplay},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


// ==============
// Audiobook MENU
// ==============
//
class AudiobookMenuGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let refToThis = this;
        let containerList = [];

        let filter_audiobook = {category: 'audiobook', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        // TODO: Separate levels and not levels => new request needed
        let requestList = [
            {title: translated_titles['audiobook'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_audiobook},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);

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

    getContainerList(minimalThumbnails, allThumbnails){
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
        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}



// ==============
// E-book MENU
// ==============
//
class EbookMenuGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_ebook = {category: 'ebook', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: translated_titles['ebook'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/ebook/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['ebook'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_ebook},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


// ========
// Dia MENU
// ========
//
//class DiaMenuGenerator extends  IndividualRestGenerator{
class DiaMenuGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_dia = {category: 'dia', playlist: '*',  tags: '*', level: '*', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: translated_titles['dia'],  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/standalone/category/dia/genre/*/theme/*/director/*/actor/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: translated_titles['dia'], rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_dia},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
    }
}


// ==================
// Entertainment MENU
// ==================
//
//class EntertainmentLevelRestGenerator extends  LevelRestGenerator{
class EntertainmentLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_entertainment = {category: 'entertainment', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/entertainment/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_entertainment},
           ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}


// ==============
// Knowledge MENU
// ==============
//
//class KnowledgeLevelRestGenerator extends  LevelRestGenerator{
class KnowledgeLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_knowledge = {category: 'knowledge', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
//            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/general/level/menu/category/knowledge/genre/*/theme/*/origin/*/decade/*/lang/" +  this.language_code},
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_knowledge},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}


// ==============
// Personal MENU
// ==============
//
class PersonalLevelRestGenerator extends  GeneralRestGenerator{

    getContainerList(minimalThumbnails, allThumbnails){
        let containerList = [];

        let filter_knowledge = {category: 'personal', playlist: '*',  tags: '*', level: 'menu', filter_on: '*', title: '*', genres:'*', themes: '*', directors: '*', actors: '*', lecturers: '*', performers: '*', origins: '*', decade: '*'};

        let requestList = [
            {title: this.container_title, rq_static: true, rq_method: "GET", rq_url: "http://" + host + port + "/collect/highest/mixed/category/{category}/playlist/{playlist}/tags/{tags}/level/{level}/filter_on/{filter_on}/title/{title}/genres/{genres}/themes/{themes}/directors/{directors}/actors/{actors}/lecturers/{lecturers}/performers/{performers}/origins/{origins}/decade/{decade}/lang/" +  this.language_code, filter: filter_knowledge},
        ];

        containerList = this.generateContainers(requestList, minimalThumbnails, allThumbnails);
        return containerList;
   }
}