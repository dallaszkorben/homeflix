/**
 * Parse a merged string into an array of objects with value, label, and not_flag
 * @param {string} mergedString - String in the format "value1_AND__NOT_value2_AND_value3"
 * @returns {Array} - Array of objects with value, label, and not_flag properties
 */
function parseMergedListElements(mergedString) {
    if (!mergedString) return [];

    // Split the string by '_AND_'
    const parts = mergedString.split('_AND_');

    // Process each part
    return parts.map(part => {
        const hasNot = part.startsWith('_NOT_');
        const value = hasNot ? part.substring(5) : part;

        return {
            value: value,
            label: value,
            not_flag: hasNot ? '_NOT_' : ''
        };
    });
}

function parseMergedDictElements(mergedString, dict) {
    if (!mergedString) return [];

    // Split the string by '_AND_'
    const parts = mergedString.split('_AND_');

    // Process each part
    return parts.map(part => {
        const hasNot = part.startsWith('_NOT_');
        const value = hasNot ? part.substring(5) : part;
        const label = dict.has(value) ? dict.get(value) : (dict[value] !== undefined ? dict[value] : '???');
        return {
            value: value,
            label: label,
            not_flag: hasNot ? '_NOT_' : ''
        };
    });
}


// -----------------------------
//
//   Search single Components
//
// -----------------------------

/**
 * Core function to create an autocomplete input field
 * @param {string} inputId - ID of the input element
 * @param {Object} options - Configuration options
 * @returns {jQuery} - The input element
 */
function createAutocompleteField(inputId, options) {
    const {
        containerClass = `custom-combobox-${inputId}`,
        withButton = false,
        autocompleteOptions = {},
        blurHandler = null
    } = options;

    // Clean up any existing elements
    $(`.combobox-toggle-${inputId}`).remove();
    $(`.${containerClass}`).children().unwrap();

    // Replace input element
    $(`#${inputId}`).replaceWith(`<input type="text" id="${inputId}" class="ui-widget-content ui-corner-all">`);
    const $input = $(`#${inputId}`);

    // Initialize autocomplete
    // Not working option
    //const finalOptions = {
    //    ...autocompleteOptions,
    //    appendTo: "#dropdowns"
    //};
    //$input.autocomplete(finalOptions);
    // Working option
    $input.autocomplete(autocompleteOptions);

    // Override the _renderItem method to apply custom styling
    $input.autocomplete("instance")._renderItem = function(ul, item) {
        return $("<li>")
            .attr("data-value", item.value || item)
            .append($("<div>").text(item.label || item).css({
                'font-family': 'inherit',
                'font-size': 'inherit'
            }))
            .appendTo(ul);
    };

    // Apply styling to the input
//    $input.css({
//    'font-family': 'inherit',
//    'font-size': 'inherit'
//    });

    // Add blur handler if provided
    if (blurHandler) {
        $input.on('blur', blurHandler);
    }

    // Add dropdown button if requested
    if (withButton) {
        $input.after(
            $('<button>', {
                tabindex: -1,
                type: 'button',
                title: 'Show All Items',
                class: `ui-button ui-widget ui-button-icon-only combobox-toggle-${inputId} noselect`,
                html: '<span class="ui-icon ui-icon-triangle-1-s"></span>'
            }).on('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();

                // Toggle dropdown visibility
                if ($input.autocomplete("widget").is(":visible")) {
                    $input.autocomplete("close");
                } else {
                    // Show all options
                    $input.focus();
                    $input.autocomplete("search", "");
                }
            }).on('mouseup', function(e) {
                e.preventDefault();
                e.stopPropagation();
            })
        );
    }

    // Add the CSS if it doesn't exist
    if (!$(`#combobox-styles-${inputId}`).length) {
        const css = `
            .${containerClass} {
                position: relative;
                display: inline-block;
                width: 100%;
                margin-bottom: 0px;
            }
            ${withButton ? `
            .combobox-toggle-${inputId} {
                position: absolute;
                top: 0;
                right: 0;
                height: 100%;
                width: 2em;
                margin: 0;
                padding: 0;
                cursor: pointer;
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
            }` : ''}
            .ui-autocomplete {
                max-height: 200px;
                overflow-y: auto;
                overflow-x: hidden;
                z-index: 9999;
            }
            #${inputId} {
                width: ${withButton ? 'calc(100% - 2em)' : '100%'};
                box-sizing: border-box;
            }
            .noselect {
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                -khtml-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }`;

        $('<style>', {
            id: `combobox-styles-${inputId}`
        }).text(css).appendTo('head');
    }

    // Wrap elements if button exists
    if (withButton) {
        $(`#${inputId}, .combobox-toggle-${inputId}`).wrapAll(`<div class="${containerClass}">`);
    } else {
        $(`#${inputId}`).wrap(`<div class="${containerClass}">`);
    }

    return $input;
}



/**
 * Creates a combobox with dictionary data
 * @param {string} inputId - ID of the input element
 * @param {Map|Object} dataDict - Dictionary of values and labels
 */
function createComboBoxWithDict(inputId, dataDict) {
    // Create array of options from the dictionary
    const options = Array.from(dataDict).map(([dictKey, dictValue]) => ({
        value: dictKey,
        label: dictValue
    }));

    // Create autocomplete options
    const autocompleteOptions = {
        source: function(request, response) {
            if (request.term === '') {
                response(options);
                return;
            }
            const matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
            response(options.filter(option =>
                matcher.test(option.label) || matcher.test(option.value)
            ));
        },
        minLength: 0,
        select: function(event, ui) {
            $(this).val(ui.item.label);
            $(this).attr('data-value', ui.item.value);
            return false;
        }
    };

    // Create blur handler
    const blurHandler = function() {
        const currentValue = $(this).val();
        if (currentValue) {
            const exactMatcher = new RegExp('^' + $.ui.autocomplete.escapeRegex(currentValue) + '$', "i");
            const exactMatch = options.find(option =>
                exactMatcher.test(option.label) || exactMatcher.test(option.value)
            );

            if (exactMatch) {
                $(this).val(exactMatch.label);
                $(this).attr('data-value', exactMatch.value);
            } else {
                const partialMatcher = new RegExp($.ui.autocomplete.escapeRegex(currentValue), "i");
                const partialMatch = options.find(option =>
                    partialMatcher.test(option.label) || partialMatcher.test(option.value)
                );

                if (partialMatch) {
                    $(this).val(partialMatch.label);
                    $(this).attr('data-value', partialMatch.value);
                } else {
                    $(this).val('');
                    $(this).attr('data-value', '');
                }
            }
        } else {
            $(this).attr('data-value', '');
        }
    };

    // Store the dictionary as data attribute
    const $input = createAutocompleteField(inputId, {
        withButton: true,
        autocompleteOptions: autocompleteOptions,
        blurHandler: blurHandler
    });

    $input.data('dataDict', dataDict);

    return $input;
}

/**
 * Creates a field with autocomplete from a list
 * @param {string} inputId - ID of the input element
 * @param {Array} dataList - List of autocomplete options
 * @param {number} minChars - Minimum characters to trigger autocomplete
 */
function createFieldWithAutocompleteFromList(inputId, dataList, minChars = 2) {
    // Create autocomplete options
    const autocompleteOptions = {
        source: function(request, response) {
            if (request.term.length >= minChars) {
                const searchTerm = request.term;
                const isUpperCase = /[A-Z]/.test(searchTerm);
                const matches = dataList.filter(item => {
                    if (isUpperCase) {
                        return item.includes(searchTerm);
                    }
                    return item.toLowerCase().includes(searchTerm.toLowerCase());
                }).sort((a, b) => {
                    const startsWithTerm = (str, term) => {
                        if (isUpperCase) {
                            return str.startsWith(term);
                        }
                        return str.toLowerCase().startsWith(term.toLowerCase());
                    };

                    const aStartsWith = startsWithTerm(a, searchTerm);
                    const bStartsWith = startsWithTerm(b, searchTerm);

                    if (aStartsWith && !bStartsWith) return -1;
                    if (!aStartsWith && bStartsWith) return 1;

                    return a.localeCompare(b);
                });

                response(matches);
            } else {
                response([]);
            }
        },
        minLength: minChars,
        select: function(event, ui) {
            const value = ui.item.value || ui.item;
            $(this).val(value);
            $(this).attr('data-value', value); // Set data-value attribute
            return false;
        }
    };

    // Create blur handler
    const blurHandler = function() {
        const currentValue = $(this).val();
        if (currentValue) {
            const isUpperCase = /[A-Z]/.test(currentValue);
            let exactMatch;
            if (isUpperCase) {
                exactMatch = dataList.find(item => item === currentValue);
            } else {
                exactMatch = dataList.find(item =>
                    item.toLowerCase() === currentValue.toLowerCase()
                );
            }

            if (exactMatch) {
                $(this).val(exactMatch);
                $(this).attr('data-value', exactMatch); // Set data-value attribute
            } else {
                const partialMatches = dataList.filter(item => {
                    if (isUpperCase) {
                        return item.includes(currentValue);
                    }
                    return item.toLowerCase().includes(currentValue.toLowerCase());
                });

                if (partialMatches.length > 0) {
                    $(this).val(partialMatches[0]);
                    $(this).attr('data-value', partialMatches[0]); // Set data-value attribute
                } else {
                    $(this).val('');
                    $(this).attr('data-value', ''); // Clear data-value attribute
                }
            }
        } else {
            $(this).attr('data-value', ''); // Clear data-value attribute
        }
    };

    // Create the field
    const $input = createAutocompleteField(inputId, {
        withButton: false,
        autocompleteOptions: autocompleteOptions,
        blurHandler: blurHandler
    });

    // Preserve the original font styling
    $input.css({
        'font-family': 'inherit',
        'font-size': 'inherit'
    });


//--

//    // Apply styling to the autocomplete menu when it's created
//    $input.on("autocompleteopen", function() {
//        $(".ui-autocomplete").css({
//            'font-family': 'inherit',
//            'font-size': 'inherit'
//        });
//
//        $(".ui-menu-item").css({
//            'font-family': 'inherit',
//            'font-size': 'inherit'
//        });
//    });


//--

    return $input;
}


/**
 * Creates a free combobox with dictionary data
 * @param {string} inputId - ID of the input element
 * @param {Map|Object} dataDict - Dictionary of values and labels
 */
function createFreeComboBoxWithDict(inputId, dataDict) {
    // Create array of options from the dictionary
    const options = Array.from(dataDict).map(([dictKey, dictValue]) => ({
        value: dictKey,
        label: dictValue
    }));

    // Create autocomplete options
    const autocompleteOptions = {
        source: function(request, response) {
            if (request.term === '') {
                response(options);
                return;
            }
            const matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
            response(options.filter(option =>
                matcher.test(option.label) || matcher.test(option.value)
            ));
        },
        minLength: 0,
        select: function(event, ui) {
            $(this).val(ui.item.label);
            $(this).attr('data-value', ui.item.value);
            return false;
        }
    };

    // Create the field
    const $input = createAutocompleteField(inputId, {
        withButton: true,
        autocompleteOptions: autocompleteOptions
    });

    $input.data('dataDict', dataDict);

    return $input;
}

// Function to get the selected value (key)
function getComboboxValue(inputId) {
    return $(`${inputId}`).attr('data-value') || '';
}

function setComboboxValue(selector, value) {
    let label = $(selector).data('dataDict').get(value)
    $(selector).val(label);
    $(selector).attr('data-value', value);
}







// -----------------------------
//
//   Search Merge Components
//
// -----------------------------


/**
 * Helper function to create a merge component with any input type
 * @param {string} inputId - ID of the input element
 * @param {Function} createInputFn - Function to create the input field
 * @param {Array} createInputArgs - Arguments to pass to the input creation function
 * @returns {Object} - Object with methods to interact with the component
 */
function createMergeComponent(inputId, createInputFn, createInputArgs) {

    // Create container
    const containerClass = `merge-container-${inputId}`;

    // Replace the original input with a container div
    $(`#${inputId}`).replaceWith(`<div id="${inputId}" class="${containerClass}"></div>`);

    // Get the container
    const $container = $(`#${inputId}`);

    // Set container style
    $container.css({
        display: 'flex',
        alignItems: 'center',
        width: '100%'
    });

    // Create the merge area
    const $mergeArea = $('<div>', {
        class: 'merge-area',
        css: {
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            flex: '1',
            marginRight: '5px',
            minHeight: '30px',
            border: '1px solid #ddd',
            borderRadius: '3px',
            padding: '2px'
        }
    });

    // Create input container
    const inputId2 = `${inputId}-input`;
    const $inputContainer = $('<div>', {
        css: {
            width: '200px',
            marginRight: '5px'
        }
    });

    // Create input element
    const $input = $('<input>', {
        id: inputId2,
        type: 'text',
        class: 'ui-widget-content ui-corner-all'
    });

    $inputContainer.append($input);

    // Create add button
    const $addButton = $('<button>', {
        class: 'merge-add-button',
        html: '➕',
        css: {
            marginRight: '5px',
            color: '#4CAF50',
            cursor: 'pointer',
            opacity: 0.5,
            border: 'none',
            background: 'none',
            fontSize: '16px',
            padding: '5px'
        },
        disabled: true
    });

    // Create remove button
    const $removeButton = $('<button>', {
        class: 'merge-remove-button',
        html: '➖',
        css: {
            color: '#f44336',
            cursor: 'pointer',
            opacity: 0.5,
            border: 'none',
            background: 'none',
            fontSize: '16px',
            padding: '5px'
        },
        disabled: true
    });

    // Append elements to container
    $container.append($mergeArea, $inputContainer, $addButton, $removeButton);

    // Initialize input field with the provided function
    createInputFn(inputId2, ...createInputArgs);

    // Add blur event to update button state when field loses focus
    $(`#${inputId2}`).on('blur', function() {
        // Small delay to ensure any autocomplete or blur handlers have finished
        setTimeout(updateButtonsState, 50);
    });

    // Apply font styling after initialization
    $(`#${inputId2}`).css({
        'font-family': 'inherit',
        'fontSize': 'inherit'
    });




    // Store selected items
    const selectedItems = [];

    // Update buttons state
    function updateButtonsState() {
        const $inputField = $(`#${inputId2}`);
        let hasValue = false;

        // For fields with data-value attribute (comboboxes)
        if ($inputField.attr('data-value') !== undefined && $inputField.attr('data-value')) {
            hasValue = $inputField.attr('data-value').trim() !== '';
        }
        // For fields without data-value attribute (autocomplete fields)
        else {
            hasValue = $inputField.val() && $inputField.val().trim() !== '';
        }

        $addButton.prop('disabled', !hasValue);
        $removeButton.prop('disabled', !hasValue);

        // Update visual state
        if (hasValue) {
            $addButton.css('opacity', 1);
            $removeButton.css('opacity', 1);
        } else {
            $addButton.css('opacity', 0.5);
            $removeButton.css('opacity', 0.5);
        }
    }

    // Add item to merge area
    function addItemToMergeArea(value, label, not_flag = '') {
        const itemId = `merge-item-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

        const $mergeElement = $('<div>', {
            id: itemId,
            class: 'merge-element',
            'data-value': value,
            css: {
                border: '1px solid #ccc',
                padding: '3px 8px',
                margin: '2px',
                display: 'flex',
                alignItems: 'center',
                borderRadius: '3px',
                background: not_flag ? '#ffeeee' : '#f9f9f9' // Different background for NOT items
            }
        });

        const $label = $('<span>', {
            /*text: (not_flag ? 'NOT ' : '') + label, // Add "NOT" prefix to label if not_flag is set*/
            text: label, // Add "NOT" prefix to label if not_flag is set
            css: {
                marginRight: '4px'
            }
        });

        const $closeButton = $('<span>', {
            html: '❌',  // Using a multiplication sign instead of ❌×➕
            css: {
                fontSize: '10px',
                borderRadius: '4px',
                fontWeight: 'bold',
                padding: '2px 2px',
                display: 'inline-block',
                border: '1px solid transparent',

                textShadow: '0 0 #ffffff',
                transition: 'all 0.2s',
                cursor: 'pointer',

                borderColor: 'rgb(167 87 87)',
                backgroundColor: 'rgb(167 87 87)',
                color: 'rgba(0, 0, 0, 0)',
            }
        });

        // Add hover effect
        $closeButton.hover(
            function() {
                $(this).css({
                    backgroundColor: '#e0e0e0',         // Slightly darker gray on hover
                    borderColor: '#000',                // Darker border on hover
                    color: '#000'                       // Black text on hover
                });
            },
            function() {
                $(this).css({
                    borderColor: 'rgb(167 87 87)',      // Back to original border color
                    backgroundColor: 'rgb(167 87 87)',  // Back to original background
                    color: 'rgba(0, 0, 0, 0)',          // Back to original color
                });
            }
        );

        $closeButton.on('click', function() {
            // Remove from DOM
            $mergeElement.remove();

            // Remove from array
            const index = selectedItems.findIndex(item => item.id === itemId);
            if (index !== -1) {
                selectedItems.splice(index, 1);
            }
        });

        $mergeElement.append($label, $closeButton);
        $mergeArea.append($mergeElement);

        // Add to selected items with not_flag
        selectedItems.push({
            id: itemId,
            value: value,
            label: label,
            not_flag: not_flag
        });
    }

    // For autocomplete fields, ensure we capture the selected value
    $(`#${inputId2}`).on('autocompleteselect', function(event, ui) {
        // Prevent default to handle the value setting ourselves
        event.preventDefault();

        // Set the value manually
        const value = ui.item.value || ui.item.label || ui.item;
        $(this).val(value);

        // For autocomplete fields without data-value attribute, set it
        $(this).attr('data-value', value);

        // Update buttons state immediately
        updateButtonsState();
    });

    // Make the button click handlers more robust
    $addButton.on('click', function() {
        const $inputField = $(`#${inputId2}`);
        const inputValue = $inputField.val();
        const dataValue = $inputField.attr('data-value') || inputValue;

        if (inputValue && inputValue.trim() !== '') {
            addItemToMergeArea(dataValue, inputValue, '');
            $inputField.val('').attr('data-value', '');
            updateButtonsState();
        }
    });

    $removeButton.on('click', function() {
        const $inputField = $(`#${inputId2}`);
        const inputValue = $inputField.val();
        const dataValue = $inputField.attr('data-value') || inputValue;

        if (inputValue && inputValue.trim() !== '') {
            addItemToMergeArea(dataValue, inputValue, '_NOT_');
            $inputField.val('').attr('data-value', '');
            updateButtonsState();
        }
    });

    // Initial state
    updateButtonsState();

    // Return an object with methods to interact with the component
    return {
        getSelectedItems: function() {
            return [...selectedItems];
        },
        getMergedValues: function() {
            if (selectedItems.length === 0) {
                return '';
            }

            // Map each item to its not_flag + value
            const mergedItems = selectedItems.map(item => {
                return item.not_flag + item.value;
            });

            // Join all items with '_AND_'
            return mergedItems.join('_AND_');
        },
        addItem: function(value, label, not_flag = '') {
            addItemToMergeArea(value, label, not_flag);
        },
        clearItems: function() {
            $mergeArea.empty();
            selectedItems.length = 0;
        },
        setItems: function(items) {
            this.clearItems();
            items.forEach(item => {
                addItemToMergeArea(item.value, item.label, item.not_flag || '');
            });
        }
    };
}

/**
 * Creates a complex element for data manipulation with a combobox and merge area
 * @param {string} inputId - ID of the input element
 * @param {Map|Object} dataDict - Dictionary of values and labels
 * @returns {Object} - Object with methods to interact with the component
 */
function createComboBoxMergeWithDict(inputId, dataDict) {
    return createMergeComponent(inputId, createComboBoxWithDict, [dataDict]);
}


/**
 * Creates a complex element for data manipulation with an autocomplete field and merge area
 * @param {string} inputId - ID of the input element
 * @param {Array} dataList - List of autocomplete options
 * @param {number} minChars - Minimum characters to trigger autocomplete
 * @returns {Object} - Object with methods to interact with the component
 */
function createFieldWithAutocompleteMergeFromList(inputId, dataList, minChars = 2) {
    return createMergeComponent(inputId, createFieldWithAutocompleteFromList, [dataList, minChars]);
}

/**
 * Creates a complex element for data manipulation with a free combobox and merge area
 * @param {string} inputId - ID of the input element
 * @param {Map|Object} dataDict - Dictionary of values and labels
 * @returns {Object} - Object with methods to interact with the component
 */
function createFreeComboBoxMergeWithDict(inputId, dataDict) {
    return createMergeComponent(inputId, createFreeComboBoxWithDict, [dataDict]);
}

