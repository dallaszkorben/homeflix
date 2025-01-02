
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

    produceContainers(){
        throw new Error("Implement produceContainers() method in the " + this.constructor.name + " class!");
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

    async showAllThumbnails(requestList, objScrollSection){
        let refToThis = this;
        let containerList = [];  // Array to store the containers
        let thumbnailListCache = [];  // Array to store the thumbnail_list results

        // Phase 1: Show only the minimal number of thumbnails - which can be seen in the window
        const INITIAL_VISIBLE_LINES = 3;    // Maximum number of lines to process initially
        const INITIAL_THUMBNAILS = 11;          // Maximum number of thumbnails per line initially

        let startedHash = this.getHistoryHash(objScrollSection);

        Generator.startSpinner();

        const initial_lines = Math.min(requestList.length, INITIAL_VISIBLE_LINES);
        for (let lineIndex = 0; lineIndex < initial_lines; lineIndex++) {
            const request = requestList[lineIndex];

            let thumbnail_list = await RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"], request["rq_data"]);
            thumbnailListCache[lineIndex] = thumbnail_list;  // Cache the result

            if(thumbnail_list.length > 0){
                let oContainer = new ObjThumbnailContainer(request["title"]);
                containerList.push(oContainer);

                const actualThumbnails = Math.min(thumbnail_list.length, INITIAL_THUMBNAILS);
                for(let thumbnail_index = 0; thumbnail_index < actualThumbnails; thumbnail_index++){
                    let thumbnail_dict = thumbnail_list[thumbnail_index];
                    let play_list = [];
                    for (let sub_index = thumbnail_index; sub_index < thumbnail_list.length; sub_index++) {
                        play_list.push(thumbnail_list[sub_index]);
                    }
                    let thumbnail = refToThis.generateThumbnail(request["rq_data"], play_list);
                    oContainer.addThumbnail(thumbnail_dict["id"], thumbnail);
                }
                objScrollSection.addThumbnailContainerObject(oContainer);
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }

        Generator.stopSpinner();
        objScrollSection.focusDefault();

        // Phase 2: Continue processing the remaining thumbnails for the first INITIAL_VISIBLE_LINES
        for (let lineIndex = 0; lineIndex < initial_lines; lineIndex++) {
            const request = requestList[lineIndex];
            let thumbnail_list = thumbnailListCache[lineIndex];  // Use cached result
            if(thumbnail_list.length > INITIAL_THUMBNAILS){
                let oContainer = containerList[lineIndex];
                await new Promise(resolve => setTimeout(resolve, 100));

                for(let thumbnail_index = INITIAL_THUMBNAILS; thumbnail_index < thumbnail_list.length; thumbnail_index++){
                    let thumbnail_dict = thumbnail_list[thumbnail_index];
                    let play_list = [];
                    for (let sub_index = thumbnail_index; sub_index < thumbnail_list.length; sub_index++) {
                        play_list.push(thumbnail_list[sub_index]);
                    }
                    let thumbnail = refToThis.generateThumbnail(request["rq_data"], play_list);
                    oContainer.addThumbnail(thumbnail_dict["id"], thumbnail);
                }
            }
        }

        // Phase 3: Process all remaining lines
        for (let lineIndex = initial_lines; lineIndex < requestList.length; lineIndex++) {
            const request = requestList[lineIndex];
            let thumbnail_list = await RestGenerator.sendRestRequest(request["rq_method"], request["rq_url"], request["rq_data"]);
            if(thumbnail_list.length > 0){
                let oContainer = new ObjThumbnailContainer(request["title"]);

                for(let thumbnail_index = 0; thumbnail_index < thumbnail_list.length; thumbnail_index++){
                    let thumbnail_dict = thumbnail_list[thumbnail_index];
                    let play_list = [];
                    for (let sub_index = thumbnail_index; sub_index < thumbnail_list.length; sub_index++) {
                        play_list.push(thumbnail_list[sub_index]);
                    }
                    let thumbnail = refToThis.generateThumbnail(request["rq_data"], play_list);
                    oContainer.addThumbnail(thumbnail_dict["id"], thumbnail);
                }

                // If meanwhile the history changed - user went back - the load of the thumbnails STOPPED
                // If a media is played, it does not change the history, sot the load is countinued !
                if( startedHash !== this.getHistoryHash(objScrollSection)){
                    return;
                }
                objScrollSection.addThumbnailContainerObject(oContainer);
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
    }

    getHistoryHash(objScrollSection){
        let levels = objScrollSection.objThumbnailController.history.getLevels();
        return (levels.link + levels.text).hashCode();
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
        if(hit["appendix"].length > 0){

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
                            (function(history_title, hierarchy_id, data_dict, thumbnail_title) {
                                return function() {
                                    return new SubLevelRestGenerator(refToThis.language_code, history_title, hierarchy_id, data_dict, thumbnail_title);
                                };
                            })(history_title, hit["id"], data_dict, thumbnail_title )
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
    constructor(menuDict, language_code, parent_thumbnail_title){
        super(language_code);
        this.menuDict = menuDict;
        this.parent_thumbnail_title = parent_thumbnail_title;
    }

    produceContainers(objScrollSection){
        const refToThis = this;
        const containerConfigList = this.menuDict.container_list ?? [];
        const containerList = [];
        let requestList = [];

        let requestType = null;

        Generator.startSpinner();
        setTimeout(function() {

            // Go through all the containers
            for (let containerDict of containerConfigList) {

                const descriptorStaticHardCodedDict = containerDict.static_hard_coded ?? null;
                const descriptorDynamicHardCodedDict = containerDict.dynamic_hard_coded ?? null;
                const descriptorDynamicQueried = containerDict.dynamic_queried ?? null;
                const containerOrder = containerDict.order ?? 0

                // Static - Hard Coded Container Definitions
                if(descriptorStaticHardCodedDict !== null){

                    const container_title_list = descriptorStaticHardCodedDict.title ?? [];
                    const container_title = eval(buildTitleFromTitleList(container_title_list));

                    const containerInstance = new ObjThumbnailContainer(container_title);

                    const thumbnailList = descriptorStaticHardCodedDict.thumbnails ?? [];

                    // Go through the thumbnails
                    for (let thumbnailDict of thumbnailList){

                        const thumbnailOrder = thumbnailDict.order ?? "";
                        const thumbnailImage = thumbnailDict.thumbnail.image ?? "";

                        const thumbnail_title_list = thumbnailDict.thumbnail.title ?? [];
                        const thumbnail_title = eval(buildTitleFromTitleList(thumbnail_title_list));

                        const descriptionImage = thumbnailDict.description.image ?? "";

                        const description_title_list = thumbnailDict.description.title = [];
                        const description_title = eval(buildTitleFromTitleList(description_title_list));

                        const historyTitleList = thumbnailDict.history.title ?? [];
                        const historyTitle = eval(buildTitleFromTitleList(historyTitleList));

                        let nextMenuDict = thumbnailDict.execution ?? {};

                        const thumbnailInstance = new Thumbnail();
                        thumbnailInstance.setImageSources({thumbnail_src: descriptionImage, description_src: thumbnailImage});
                        thumbnailInstance.setTitles({main: description_title, thumb: thumbnail_title, history: historyTitle});
                        thumbnailInstance.setFunctionForSelection({
                            "single":
                                {
                                    "menu":
                                    (function(next_menu_dict, thumbnail_title) {
                                        return function() {
                                            return new GeneralRestGenerator(next_menu_dict, refToThis.language_code, thumbnail_title);
                                        };
                                    })(nextMenuDict, thumbnail_title)
                                },
                            "continuous": []
                        });
                        containerInstance.addThumbnail(thumbnailOrder, thumbnailInstance);
                        requestType = "static";

                    }
                    containerList.push(containerInstance);

                // Dynamic - Hard Coded Container Definitions
                }else if(descriptorDynamicHardCodedDict !== null){
                    const container_title_list = descriptorDynamicHardCodedDict.title ?? [];
                    const container_title = eval(buildTitleFromTitleList(container_title_list));

                    const data = descriptorDynamicHardCodedDict.data ?? {};
                    const requestDict = descriptorDynamicHardCodedDict.request ?? {static: true, method: "GET", protocol: "http", url: ""};
                    const rq_static = requestDict.static;
                    const rq_method = requestDict.method;
                    const rq_protocol = requestDict.protocol;
                    const rq_path = requestDict.path;

                    let rq_data = {}
                    for( const[key, value] of Object.entries(data)){
                        rq_data[key] = value;
                    };
                    rq_data["lang"] = refToThis.language_code;

                    const request = {title: container_title, rq_static: rq_static, rq_method: rq_method, rq_url: rq_protocol + "://" + host + port + rq_path, rq_data: rq_data};
                    requestList.push(request);


                    requestType = "dynamic";

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

                    let pre_rq_data = {}
                    for( const[key, value] of Object.entries(pre_query_data_dict)){
                        pre_rq_data[key] = value;
                    };
                    pre_rq_data["lang"] = refToThis.language_code;

                    let rq_data = {}
                    for( const[key, value] of Object.entries(query_data_dict)){
                        rq_data[key] = value;
                    };
                    rq_data["lang"] = refToThis.language_code;

                    const container_title_list = query_loop_dict.title ?? [];
                    const response = $.getJSON({ method: pre_rq_method, url: pre_rq_protocol + "://" + host + port + pre_rq_path, data: pre_rq_data, async: pre_rq_assync});
                    if(response.status == 200 && response.responseJSON["result"]){

                        // In case of DICT list response from the pre-request
                        if(query_data_dict_map_dict !== null){

                            for (let data_dict of response.responseJSON["data"]){
                                let local_rq_data = {...rq_data};
                                for( const[key, value] of Object.entries(query_data_dict_map_dict)){
                                    local_rq_data[key] = data_dict[value];
                                }
                                const title = eval(buildTitleFromTitleList(container_title_list));
                                let request = {title: title, rq_static: rq_static, rq_method: rq_method, rq_url: rq_protocol + "://" + host + port + rq_path, rq_data: local_rq_data};
                                requestList.push(request);
                            }

                            requestType = "dynamic";

                        // In case of VALUE list response from the pre-request
                        }else if(query_data_list_map_value !== null){

                            for (let data_value of response.responseJSON["data"]){
                                let local_rq_data = {...rq_data};
                                local_rq_data[query_data_list_map_value] = data_value;
                                const title = eval(buildTitleFromTitleList(container_title_list));
                                const request = {title: title, rq_static: rq_static, rq_method: rq_method, rq_url: rq_protocol + "://" + host + port + rq_path, rq_data: local_rq_data};
                                requestList.push(request);
                            }

                            requestType = "dynamic";
                        }
                    }
                }
            }

            if(requestList && requestList.length > 0){
                refToThis.showAllThumbnails(requestList, objScrollSection);
            }

            if(requestType === "static"){
                containerList.forEach(oContainer => {
                    objScrollSection.addThumbnailContainerObject(oContainer);
                });
                Generator.stopSpinner();
                objScrollSection.focusDefault();
            }

        },1);
    }
}


// -----------------------
// SubLevel REST Generator
// -----------------------
//
class SubLevelRestGenerator extends  RestGenerator{
    constructor(language_code, container_title, hierarchy_id, data_dict, parent_thumbnail_title){
        super(language_code);
        this.container_title = container_title;
        this.hierarchy_id = hierarchy_id;
        this.data_dict = data_dict;
        this.parent_thumbnail_title = parent_thumbnail_title;
    }

    produceContainers(objScrollSection, minimalThumbnails, allThumbnails){

        this.data_dict['card_id'] = this.hierarchy_id;
        let requestList = [
            {title: this.container_title,  rq_method: "GET", rq_url: "http://" + host + port + "/collect/next/mixed", rq_data: this.data_dict},
        ];

        this.showAllThumbnails(requestList, objScrollSection)
    }
}



function buildTitleFromTitleList(inputList) {
    if (!Array.isArray(inputList) || inputList.length === 0) {
        return '';
    }

    const parts = inputList.map(item => {
        // Handle text type
        if ('text' in item) {
            return JSON.stringify(item.text);
        }

        // Handle variable type
        if ('variable' in item) {
            const variable = item.variable;
            return variable;
        }

        // Handle translator type
        if ('trans' in item) {
            const trans = item.trans;
            const key = trans.key;

            if (trans.translator && trans.translator !== null) {
                return trans.translator + `["${key}"]`;
            } else {
                return ``;
            }
        }

        // Handle dictionary type
        if ('dict' in item) {
            const dict = item.dict;
            const key = dict.key;

            if (dict.translator && dict.translator !== null) {
                return dict.translator + `[data_dict["${key}"]]`;
            } else {
                return `data_dict["${key}"]`;
            }
        }

        return '';
    });

    // Join all parts with ' + ' and return
    return parts.filter(part => part !== '').join(' + ');
}
