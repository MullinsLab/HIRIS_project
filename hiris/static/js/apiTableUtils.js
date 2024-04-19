class apiTable{
    // Object to hold information about a table

    dataTableElement = undefined;           // The data table element
    dataTable = undefined;                  // The data table object
    resetFiltersLink = undefined;           // The reset filters link
    searchBox = undefined;                  // The search box object
    columns = [];                           // The columns to display
    dom = undefined;                        // The dom information to pass to the table
    ajax = undefined;                       // The ajax URL to get data from
    filters = [];                           // The filters used to modify the data
    filtersByColumn = {};                   // The filters used to modify the data, by column

    constructor(args){
        // Set up the table stuff

        var dataTableName = args.dataTableName || "DataTable";
        var searchBoxName = args.searchBoxName || "SearchBox";
        var resetFiltersLinkName = args.resetFiltersLinkName || "resetFilters";

        // Make sure that our elements exist
        if ($(`#${dataTableName}`).length) {
            this.dataTableElement = $(`#${dataTableName}`);
        }
        else {
            throw `Could not find data table with id ${dataTableName}`
        }

        if ($(`#${searchBoxName}`).length) {
            this.searchBox = $(`#${searchBoxName}`);

            var table = this;
            this.searchBox.on("keyup search input paste cut", function(e) {
                table.search(this.value);
            });
        }

        if ($(`#${resetFiltersLinkName}`).length) {
            this.resetFiltersLink = $(`#${resetFiltersLinkName}`);
            this.resetFiltersLink.click(this.resetFilters.bind(this));
        }

        // Set up the columns
        for (var columnIndex = 0; columnIndex < args.columns.length; columnIndex++) {
            this.columns.push(new column(apiTable, columnIndex, args.columns[columnIndex]));
        }

        // Set up simple attributes
        this.dom = args.dom || "<'row'<'col-sm-12 text-center'i>><'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'p>><'row'<'col-sm-12'tr>>";
        this.ajax = args.ajax;

        // Build the table
        this.buildTable();

        // Set up the filters
        if (args.filters) {
            for (var filterIndex = 0; filterIndex < args.filters.length; filterIndex++) {
                var filter_object = new filter(this, args.filters[filterIndex])
                this.filters.push(filter_object);
                this.filtersByColumn[filter_object.columnIndex] = filter_object;
                // this.filters.push(new filter(this, args.filters[filterIndex]));
            }
        }

        this.updateFilters();
    }

    buildTable(){
        // Build the table

        var args = {};

        if (this.ajax) {
            args.serverSide = true;
            args.ajax = this.ajax;
        };

        args.columns = this.columnsForTable();
        args.dom = this.dom;

        this.dataTable = this.dataTableElement.DataTable(args);

        // set up the tooltips whenever drawing the table
        this.dataTable.on( 'draw', function () {
            $('[data-toggle="tooltip"]').tooltip()
        });
    }

    columnsForTable(){
        // Return the columns in a format that the table can use

        var columns = [];

        for (var columnIndex = 0; columnIndex < this.columns.length; columnIndex++) {
            columns.push(this.columns[columnIndex].forTable());
        }

        return columns;
    }

    search(value) {
        this.dataTable.search(value).draw();
    }

    updateFilters() {
        // Update the filters

        for (var filterIndex = 0; filterIndex < this.filters.length; filterIndex++) {
            this.filters[filterIndex].getData();
        }
    }

    processFilters() {
        // Process the filters

        var filters = this.combinedFiltersByIndex();
        var triggerDraw = false;

        for (var column in filters) {
            if (this.filtersByColumn[column].single) {
                if (filters[column][0] == "__ALL__" || filters[column].length == 0) {
                    this.dataTable.column(column).search("", true, false);
                }

                else {
                    this.dataTable.column(column).search(filters[column].join("|"), true, false);
                }
                
                triggerDraw = true;
            }

            else {
                this.dataTable.column(column).search(filters[column].join("|"), true, false);
                triggerDraw = true;
            };
        }

        if (triggerDraw) {
            this.updateFilters();
            this.dataTable.draw();
        }
    }

    columnIndex(name) {
        // Get the index of a column by name

        for (var columnIndex = 0; columnIndex < this.columns.length; columnIndex++) {
            if (this.columns[columnIndex].name == name) {
                return columnIndex;
            }
        }

        return undefined;
    }

    combinedFilters() {
        // Get the combined filters

        var filters = {};
        
        for (var filterIndex = 0; filterIndex < this.filters.length; filterIndex++) {
            var filter = this.filters[filterIndex];
            filters[filter.name] = filter.currentValues;
        }

        return filters;
    }

    combinedFiltersByIndex() {
        // Get the combined filters by index

        var filters = {};

        for (var filterIndex = 0; filterIndex < this.filters.length; filterIndex++) {
            var filter = this.filters[filterIndex];
            filters[filter.columnIndex] = filter.currentValues;
        }

        return filters;
    }

    resetFilters() {
        // Reset the filters

        for (var filterIndex = 0; filterIndex < this.filters.length; filterIndex++) {
            this.filters[filterIndex].reset();
        }

        this.searchBox.val("");
        this.dataTable.search("")

        this.updateFilters();
        this.processFilters();
    }
}

class column {
    // Object to hold information about a column

    name = undefined;                       // The name of the column
    title = undefined;                      // The title of the column
    data = undefined;                       // The data to display in the column
    orderable = undefined;                  // Whether or not the column is orderable
    visible = undefined;                    // Whether or not the column is visible
    searchable = undefined;                 // Whether or not the column is searchable
    render = undefined;                     // A function to render the data
    width = undefined;                      // The width of the column
    className = undefined;                  // The class of the column
    objectField = undefined;                // The attribute to return when rendering an object
    editURL = undefined;                    // The URL to edit the object
    linkURL = undefined;                    // The URL to link to
    renderAs = undefined;                   // The type of data to render: values: YesNo
    subValues = undefined;                  // The values to substitute when rendering
    apiTable = undefined;                   // The apiTable object that this filter is attached to
    tableIndex = undefined;                 // The index of the column in the table
    buttonIcon = undefined;                 // The icon to use for the button
    toolTip = undefined;                    // The tooltip to use for the button
    filterValue = undefined;                // The value to use when deciding to show the field
    filterIf = undefined;                   // The test for the value
    nullValue = undefined;                  // The value to display when the data is null

    constructor(apiTable, columnIndex, args){
        // Set up the column stuff

        if (typeof args == "string") {
            args = {name: args};
        }

        this.name = args.name;
        this.title = args.title || toTitleCase(this.name);
        this.data = args.data || this.name;
        if (args.orderable != undefined) {this.orderable = args.orderable} else {this.orderable = true};
        if (args.visible != undefined) {this.visible = args.visible} else {this.visible = true};
        this.width = args.width || undefined;
        this.className = args.className || "";
        this.apiTable = apiTable;
        this.tableIndex = columnIndex;
        this.buttonIcon = args.buttonIcon;
        this.toolTip = args.toolTip;
        this.nullValue = args.nullValue;

        if (args.filterValue && args.filterIf) {    
            this.filterValue = args.filterValue;
            this.filterIf = args.filterIf;
        }

        // Special kinds of columns
        if (args.objectField) {
            this.objectField = args.objectField;
            this.render = this.renderObjectField.bind(this);
        }
        else if (args.editURL) {
            this.orderable = false;
            this.searchable = false;
            this.editURL = args.editURL;
            this.render = this.renderEditButton.bind(this);
        }
        else if (args.linkURL) {
            this.linkURL = args.linkURL;
            this.render = this.renderLink.bind(this);
        }
        else if (args.renderAs) {
            this.renderAs = args.renderAs;
            this.render = this.renderFunction.bind(this);
        }
        else if (args.subValues) {
            this.subValues = args.subValues;
            this.render = this.renderFunction.bind(this);
        }
    };

    renderFunction(data, type, row, met){
        // Generic render function

        if (this.renderAs == "YesNo") {
            return this.renderYesNo(data);
        }
        else if (this.subValues) {
            return this.renderSubValues(data);
        }
    };

    renderSubValues(value){
        // Resolve a value to a label for rendering

        if (value in this.subValues) {
            return this.subValues[value];
        }
    };

    renderYesNo(value){
        // Resolve a value as a yes or no for rendering

        if (value) {
            return "Yes";
        }
        else {
            return "No";
        }
    };

    renderObjectField(data, type, row, meta){
        // Render the data as an object field
        var field = this.objectField;
        
        if (data == null) {
            if (this.nullValue) {
                return this.nullValue;
            }
            else {
                return "";
            }
        }
        else if (Array.isArray(data)){
            return data.sort((a, b) => a[field].localeCompare(b[field])).map(object => object[field]).join(", ");
        }
        else {
            return data[field];
        };
    };

    renderLink(data, type, row, meta){
        // Render the data with a link

        var linkURL = subRowValue(row, this.linkURL);
        return `<a href="${linkURL}" >${row[this.name]}</a>`;
    };

    renderEditButton(data, type, row, meta){
        // Render the data as an edit button

        if (this.filterValue && this.filterIf) {
            var testValue = subRowValue(row, this.filterValue);

            if (! testValue || testValue === null) {return ""};
            
            if (this.filterIf == "isUWEmail" && isUWEmail(testValue)) {
                return "";
            }
        }

        var editURL = subRowValue(row, this.editURL);
        var toolTipBit = "";

        if (this.toolTip) {
            toolTipBit = ` data-toggle="tooltip" data-placement="left" title="${this.toolTip}"`;
        };

        if (this.buttonIcon && this.buttonIcon.toLowerCase() == "lock") {
            return `<a href="${editURL}" ><i class="fa fa-lock"/${toolTipBit}></a>`;
        }

        return `<a href="${editURL}" ><i class="fa fa-pencil"/${toolTipBit}></a>`;
    }

    forTable(){
        // Return the column object in a format that the table can use

        return {
            name: this.name,
            title: this.title,
            data: this.data,
            searchable: this.searchable,
            orderable: this.orderable,
            visible: this.visible,
            render: this.render,
            width: this.width,
            className: this.className
        };
    }
}


class filter {
    // Ojbect to hold information about a filter

    name = undefined;                       // The name of the filter
    title = undefined;                      // The title of the filter (displayed above the filter list)
    displayAs = undefined;                  // The type of control to display as: values: YesNoAll
    containerElement = undefined;           // The element to put the filter container in
    listElement = undefined;                // The element to put the filter list in
    sortElement = undefined;                // The element to use to sort the list
    labelField = undefined;                 // The field to get the lable from when rendering an object
    countField = undefined;                 // The field to get the count from when rendering an object
    values = undefined;                     // The values to use when rendering a non Ajax filter
    ajax = undefined;                       // The ajax URL to get data from
    apiTable = undefined;                   // The apiTable object that this filter is attached to
    sorting = undefined;                    // The sorting to use when rendering an object
    listHeight = undefined;                 // The height of the list
    data = undefined;                       // The data for the filter
    currentValues = [];                     // The values that are currently selected
    columnIndex = undefined;                // The index of the column that this filter is attached to
    single = undefined;                     // Whether or not the filter is a single select filter
    filterString = undefined;               // The string to use to filter the data
    isRendered = false;                    // Whether or not the filter has been rendered

    constructor(apiTable, args){
        // Set up the filter stuff

        // Make sure that the filterContainer exist
        if ($(`#${args.name}FilterContainer`).length) {
            this.containerElement = $(`#${args.name}FilterContainer`);
        }
        else {
            throw `Could not find filter container with id ${args.name}FilterContainer`
        }

        this.name = args.name;
        this.apiTable = apiTable;
        this.title = args.title || toTitleCase(this.name);
        this.displayAs = args.displayAs || "AjaxList";
        this.values = args.values;
        this.ajax = args.ajax;
        this.labelField = args.labelField || this.name;
        this.countField = args.countField || "count";
        this.sorting = args.sorting || "count";
        this.listHeight = args.listHeight || "full";
        this.columnIndex = apiTable.columnIndex(this.name);
        // this.single = args.single || false;
        this.single = (args.single || ["YesNoAll"].includes(this.displayAs)) || false;

        this.createElements();
    }

    createElements(){
        if (this.displayAs == "YesNoAll") {
            this.createElementsYesNo({all: true});
        }
        else if (this.displayAs == "AjaxList") {
            this.createElementsAjaxList();
        }
    }

    createElementsYesNo(args){
        // Set up the elements for a YesNoAll filter
        // Should be reworked as a generic radio button filter

        var filterElements = 
        `<div style="margin-bottom: .5rem;"><h6>${this.title}</h6>
            <div id="${this.name}FilterList" class="btn-group btn-group-toggle btn-group-sm" data-toggle="buttons">
            </div>
        </div>`;

        this.containerElement.append(filterElements);

        this.listElement = $(`#${this.name}FilterList`);
        this.listElement.on("click", ".virofilter", this.click.bind(this));
    }

    createElementsAjaxList(){
        // Set up the elements for an AjaxList filter

        var filterGroupClass;
        switch (this.listHeight) {
            case "full":
                filterGroupClass = "filterGroup";
                break;
            case "half":
                filterGroupClass = "filterGroupHalf";
                break;
        }
        
        var filterElements = `<div style="margin-bottom: .5rem;"><h6 style="display:inline;">${this.title}</h6><a href="javascript:void(0);" id="${this.name}Sort"> Sort by Name</a></div>`
        filterElements += `<div id="${this.name}FilterList" class="btn-group-vertical btn-group-toggle btn-group-sm btn-block ${filterGroupClass}" data-toggle="buttons"></div>`
        this.containerElement.append(filterElements);

        this.listElement = $(`#${this.name}FilterList`);
        this.listElement.on("click", ".virofilter", this.click.bind(this));

        this.sortElement = $(`#${this.name}Sort`);
        this.sortElement.click(this.toggleSort.bind(this));
    }

    getData(){
        // Get the data for the filter

        if (! this.ajax) {
            this.render();
            return;
        }

        var filterString = this.getFilterString();

        if (this.data != undefined && this.filterString == filterString) {
            return false;
        }

        var filter = this;
        $.ajax({
            url: `${this.ajax}${filterString}`,
            dataType: "json",
            success: function(data){
                filter.render(data);
            }
        });

        this.filterString = filterString;
        return true;
    }

    getFilterString(){
        // Get the filter string

        var filterStrings = [];
        var filters = this.apiTable.combinedFilters();

        for (var filterName in filters) {
            if (filterName != this.name && filters[filterName].length) {
                if (! filters[filterName].includes("__All__")) {
                    filterStrings.push(`${filterName}=${filters[filterName].join("|")}`);
                }
            }
        }

        if (filterStrings.length == 0) {return ""}

        return `?${filterStrings.join("&")}`;
    }

    render(data){
        // Render the filter

        if (this.displayAs == "YesNoAll") {
            this.renderFixed(data);
        }
        else if (this.displayAs == "AjaxList") {
            this.renderAjaxList(data);
        }

        this.isRendered = true;
    }

    renderFixed(data) {
        // Render filter with fixed values

        if (this.isRendered) {return}

        var defaultValues = {};
        var defaultValue = "";

        if (this.displayAs == "YesNoAll") {
            defaultValues = {Yes: "Yes", No: "No", All: "__All__"};
            defaultValue = this.currentValues[0] || "__All__";
        }

        for (var value in defaultValues) {
            var checked = defaultValue == defaultValues[value] ? "checked" : ""
            var id = (this.name + "_" + defaultValues[value]).replace(/[^A-Z0-9]/ig, "_")
            
            this.listElement.append(  
                `<label class="btn btn-outline-primary shadow-none active">
                    <input class="virofilter" id="sequenceall" type="radio" id="${id}" name="${this.name}" autocomplete="off"  value="${this.values[value] || defaultValues[value]}" ${checked}> ${value}
                </label>`);
        }
    }

    renderAjaxList(data) {
        // Render the filter as a list

        if (data == undefined) {
            if (this.data) {data = this.data}
            else {throw `Got render request for ${this.name}, but not given data, and have no stored data`}
        }

        // Make sure null sorts last, alphabetically
        if (this.sorting == "label") {
            data = data.sort((a, b) => a[this.labelField]===null ? 1 : (a[this.labelField].localeCompare(b[this.labelField]) || b[this.countField] - a[this.countField]));
        }
        else if (this.sorting == "count") {
            if (["number", "boolean"].includes(typeof(data[0][this.labelField]))) {
                data = data.sort((a, b) => b[this.countField] - a[this.countField]);
            }
            else {
                data = data.sort((a, b) => b[this.countField] - a[this.countField] || (a[this.labelField]===null ? -1 : a[this.labelField].localeCompare(b[this.labelField])));
            }
        }

        this.data = data;

        this.listElement.empty();

        var type = "checkbox";
        if (this.single) {
            type = "radio";

            // Get total count
            var totalCount = 0;
            for (var dataIndex = 0; dataIndex < data.length; dataIndex++) {
                totalCount += data[dataIndex][this.countField];
            };

            var badge = 'bg-dark';
            var checked = ! this.currentValues.length || this.currentValues.includes("__All__") ? " checked" : "";
            var active = checked ? " active" : "";

            this.listElement.append(`<label class="btn btn-outline-secondary shadow-none d-flex justify-content-between align-items-center text-left${active}">` +
                            `<input class="virofilter" type="${type}" id="${(this.name + "___All__").replace(/[^A-Z0-9]/ig, "_")}" name="${this.name}" autocomplete="off" value="__ALL__"${checked}><i>All</i>`+
                            `&nbsp;&nbsp;&nbsp;&nbsp;<span class="badge rounded-pill ${badge}">${totalCount.toLocaleString()}</span>` +
                            `</label>`);
        };

        for (var dataIndex = 0; dataIndex < data.length; dataIndex++) {
            var label = data[dataIndex][this.labelField]===null ? "<i>None</i>" : data[dataIndex][this.labelField];
            var count = data[dataIndex][this.countField];
            var safeId = (this.name + "_" + label).replace(/[^A-Z0-9]/ig, "_");
            var checked = this.currentValues.includes(label) ? " checked" : "";
            var active = checked ? " active" : "";
            var badge = (count == 0 && value.checked ? 'bg-danger' : 'bg-dark');

            this.listElement.append(`<input class="virofilter btn-check" type="${type}" id="${safeId}" name="${this.name}" autocomplete="off" value="${label}"${checked}>`+
                            `<label class="btn btn-outline-secondary shadow-none d-flex justify-content-between align-items-center text-left${active}" for="${safeId}">` +
                            `${label}&nbsp;&nbsp;&nbsp;&nbsp;<span class="badge rounded-pill ${badge}">${count.toLocaleString()}</span>` +
                            `</label>`);
        }
    }

    toggleSort() {
        // Switch the sorting of the filter

        if (this.sorting == "label") {
            this.sorting = "count";
            this.sortElement.text(" Sort by Name");
        }
        else if (this.sorting == "count") {
            this.sorting = "label";
            this.sortElement.text(" Sort by Count");
        }

        this.render();
    }

    click() {
        // Handle a click on the filter

        console.log("click")

        this.currentValues = [];
        
        var currentValues = this.currentValues;
        this.listElement.find("input:checked").each(function(){
            currentValues.push($(this).val());
        });

        this.apiTable.processFilters();
    };

    reset() {
        // Reset the filter

        this.isRendered = false;
        this.listElement.empty();
        this.currentValues = [];
    };
};

function subRowValue(row, string) {
    // Sub a row value into a string

    if (! string) {return string}

    var variableRegEx = /\(.*:.*\)/
    var matches = string.match(variableRegEx);

    for (var matchIndex = 0; matchIndex < matches.length; matchIndex++) {
        var match = matches[matchIndex];
        var [type, variable] = match.replace("(", "").replace(")", "").split(":");
        var value = "";

        if (type == "row") {
            value = row[variable];
        }
        
        if (value === null || value === undefined) {
            value = "";
        }

        return string.replace(match, value);
    };
};


function toTitleCase(str) {
    // adjusted from https://stackoverflow.com/questions/196972/convert-string-to-title-case-with-javascript

    if (str == undefined || str == "") {return undefined}

    if (str.includes("_")) {
        str = str.replace(/_/g, " ");
    };

    if (str.toUpperCase() == str) {
        // deal with all caps
        str = str.toLowerCase();
    }
    else {
        // deal with camelCase
        str = str.replace(/([a-z])([A-Z])/g, '$1 $2');
    };

    return str.replace(
        /\w\S*/g,
        function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
};


function isUWEmail(email) {
    // Check if an email is a UW email

    if (! email) {return undefined}

    var UWDomains = ["uw.edu", "washington.edu"]

    for (var domainIndex in UWDomains) {
        var domain = UWDomains[domainIndex];
        if (email.trim().toLowerCase().endsWith(domain)) {
            return true;
        }
    };

    return false;
};