// code here when the document is ready.
$( document ).ready(function() {
    
    // set csrftoken value
    window.csrftoken = getCookie('csrftoken');
    
    if ($("span.data-set-limit").length) {
        window.dataSetLimiter = new DataSetLimiter();
    }

    console.log("HiRIS is ready");
        
});


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

// Set default values for future Ajax requests. Its use is not recommended, but necessary for Django to function with CSRF protection
function ajaxSetup(csrftoken){
	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
				// Send the token to same-origin, relative URLs only.
				// Send the token only if the method warrants CSRF protection
				// Using the CSRFToken value acquired earlier
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			}
		}
	});
}


class DataSetLimiter {
    // Class to manage limiting data sets in exports and data views
    
    buttons = [];               // Array of buttons that will set the data set limit
    dataSets = [];              // Array of data sets that can be limited
    modal = undefined;          // Modal that will be used to set the data set limit
    form = undefined;           // Form that will be used to set the data set limit

    constructor() {
        this.get();
        
        this.modal = $("#dataSetModal");
        this.form = $("#dataSetModalForm");
        
        $("#dataSetModalSubmit").click(function() {window.dataSetLimiter.save()});
        $("#dataSetModalClear").click(function() {window.dataSetLimiter.clear()});
        
        console.log("DataSetLimiter initialized");
    }

    get() {
        let self = this;

        $.ajax({ 
            url: "/api/limit_data_sets",
            method: 'GET', 
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin',
            success: function(response) { 
                self.dataSets = response;
                self.setButtons();
            }, 
            error: function(xhr, status, error) { 
                console.log("Failed to load data sets");
            } 
        }); 
    }

    post(data){
        let self = this;
        console.log({data_sets: data});
        $.ajax({
            url: "/api/limit_data_sets",
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin',
            data: {data_sets: data},
            success: function(response) {
                self.dataSets = response;
                self.setButtons();
                self.hide();
            },
        })
    }

    setButtons() {
        let buttonHTML = `<button type="button" class="btn btn-sm btn-outline-primary data-set-limit RELOAD_REPLACER">Set Data Set Limit</button>`;
        
        for (let span of $("span.data-set-limit")) {
            let replacer = $(span).hasClass("data-set-limit-reload") ? "data-set-limit-reload" : "";

            $(span).html(buttonHTML.replace("RELOAD_REPLACER", replacer));
        };

        this.buttons = $(".data-set-limit:button");
        this.buttons.click(function() {
            window.dataSetLimiter.show();
        });
    }

    show() {
        this.form.html(this.renderHTML());
        this.modal.modal("show");
    }

    hide() {
        this.modal.modal("hide");
    }

    renderHTML() {
        let html = "";

        for (let dataSet of this.dataSets) {
            html += `<div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="dataSet${dataSet.id}" ${dataSet.selected ? "checked" : ""}>
                <label class="form-check-label" for="dataSet${dataSet.id}">${dataSet.name}</label></div>`
        }

        return html;
    }

    save() {
        let data = [];

        for (let dataSet of this.dataSets) {
            if ($(`#dataSet${dataSet.id}`).prop("checked")) {
                data.push(dataSet.id);
            }
        };

        this.post(data.join());
    }

    clear() {
        let data = [];

        for (let dataSet of this.dataSets) {
            data.push(dataSet.id);
        };

        this.post(data.join());
    }
}