// Variables for the do_import_scheme import_wizard page

class ImportScheme {
    id;                     // ID from the database
    items = [];             // ImportSchemeItem objects
    base_url;               // Base URL for loading from the system
    accordion_container;    // ID of the DOM object being used to hold the accordion
    // _this = this;

    constructor(args){
        // Set up the ImportScheme and get its items
        this.id = args.id;
        this.base_url = args.base_url;
        this.accordion_container = args.accordion_container;

        this.get_items();
    };

    find_item_by_id(id){
        /// Get an item from the list by the database id
        return this.items.find(item => item.id == id);
    };

    find_item_by_model(model){
        /// Get an item from the list by model name
        return this.items.find(item => item.model == model);
    };

    get_items(){
        // Get a list of import_scheme_items from the backend
        $.ajax(this.base_url+'/list', {
            // pass this to caller so it's referrable inside the done function
            caller: this,
            dataType: 'json',
            cache: false,
        }).done(function(data){
            let items = data.import_scheme_items;
            for (let item in items){
                this.caller.items.push(new ImportSchemeItem({id: items[item], index: this.caller.items.length, parent: this.caller}))
                
                // Set up a base_accordion_X as a placeholder for the accordion block
                $(this.caller.accordion_container).append("<div id='base_accordion_" + (this.caller.items.length-1) + "'>");
            };
        });
    };
};

class ImportSchemeItem{
    id;                     // ID from the database or name.  Used for loading
    index;                  // Index number of the list of items from the parent
    name;                   // Name to be displayed in the accoridon button
    description;            // Description to be displayed in the accordion body - placeholder for HTML form or whatnot
    form;                   // The form to use to collect information about this item
    urgent = false;         // Is the Item urgent, meaning that it needs to be dealt with before the import can happen
    start_expanded;         // If true, the accordion will start in an expanded state
    dirty;                  // Indicates that the item is dirty and needs to be rerendered
    parent;                 // ImportScheme this Item belongs to
    selectpicker;           // If true, executes $('.selectpicker').selectpicker();
    tooltip;                // If true, executes $('[data-toggle="tooltip"]').tooltip()
    fields = []             // Holds a list of all the fields in this item
    model;                  // name of the model this item represents

    // objects that corrispond with the dom objects for this item
    accordion;
    button;
    collapse;
    body;

    constructor(args){
        this.id = args.id;
        this.index = args.index;
        this.parent = args.parent;

        this.load();
    };

    load(args){
        // Load the ImportSchemeItem from the backend
        let load_url = this.parent.base_url+'/'+this.id;

        $.ajax(load_url, {
            // pass this to caller so it's referrable inside the success function
            caller: this,
            dataType: 'json',
            cache: false,
        }).done(function(data){
            this.caller.set_with_dirty({field: 'name', value: data.name});
            this.caller.set_with_dirty({field: 'description', value: data.description});
            this.caller.set_with_dirty({field: 'form', value: data.form});
            this.caller.set_with_dirty({field: 'urgent', value: data.urgent});
            this.caller.set_with_dirty({field: 'start_expanded', value: data.start_expanded});
            this.caller.set_with_dirty({field: 'selectpicker', value: data.selectpicker});
            this.caller.set_with_dirty({field: 'tooltip', value: data.tooltip});
            this.caller.set_with_dirty({field: 'model', value: data.model});
            this.caller.set_with_dirty({field: 'fields', value: data.fields});

            this.caller.render();
        })
    };

    set_with_dirty(args){
        // Sets the field value if different from current, and if so sets dirty to true
        if ((Array.isArray(args.value) && ! arraysEqual(args.value, this[args.field])) || (! Array.isArray(args.value) && this[args.field] != args.value)){
            this[args.field] = args.value;
            this.dirty=true;
        }
    }

    render(args){
        // Create the structure of the accoridion

        // If the accordion item doesn't exist yet, create it
        if (! $('#accordion_'+this.id).length){
            // Replace base_accordion_X with the actual accordion from template
            $("#base_accordion_"+this.index).replaceWith(ITEM_TEMPLATE.replaceAll("!ACCORDION_ID!", this.id))

            // Assign the dom object refrences for this item
            this.accordion = $('#accordion_'+this.id)
            this.button = $('#button_'+this.id);
            this.collapse = $('#collapse_'+this.id);
            this.body = $('#body_'+this.id);
        };

        // If the item isn't dirty, no reason to render it
        if (! this.dirty){
            return 1;
        };
        
        this.button.html(this.name);

        let body_bit = "";
        if (this.description){body_bit += this.description}
        if (this.form){
            if (this.description){body_bit += "<br><br>"}
            body_bit += this.form
        }
        this.body.html(body_bit);

        // Set the propper css classes and open/close if item is urgent
        if (this.urgent){
            this.accordion.removeClass('border-primary');

            this.accordion.addClass('border-danger');
            this.button.addClass('accordion-urgent-button');
        } else {
            this.accordion.removeClass('border-danger');
            this.button.removeClass('accordion-urgent-button');

            this.accordion.addClass('border-primary');
        };

        // Open or close accordion based on start_expanded
        if (this.start_expanded){
            this.collapse.collapse('show');
        } else {
            this.collapse.collapse('hide');
        };
        
        if (this.selectpicker){
            $('.selectpicker').selectpicker();
        };

        if (this.tooltip){
            $('[data-toggle="tooltip"]').tooltip()
        };

        // Attach ajax function to submit the form
        if (this.form){
            $("#item_form_"+this.model).submit(function (event) {
                event.preventDefault();

                let model = window.import_scheme.find_item_by_model($(this).attr("data-model"));

                let form_data = {
                    csrfmiddlewaretoken: getCookie('csrftoken'),
                };

                if ($(this).attr("data-file_saved")){
                    form_data["---file_saved---"] = $(this).attr("data-file_saved");
                };

                for (let field_index in model.fields){
                    let field = model.fields[field_index];
                    
                    if($("#file_field_" + field).attr("data-is_radio")){
                        form_data[field] = $("#file_field_" + field + " input:radio:checked").val()
                    }
                    else if($("#file_field_" + field).attr("data-is_dropdown")){
                        form_data[field] = $("#file_field_" + field).find(":selected").val()
                    }
                    else{
                        let field_name = field.split("__-__")[1];
                    
                        form_data[field_name + ":file_field"] = $("#file_field_"+field).find(":selected").val();

                        form_data[field_name + ":file_field_raw_text"] = $("#file_field_" + field + "_raw_text").val();

                        form_data[field_name + ":file_field_first_1"] = $("#file_field_" + field + "_first_1").val();
                        form_data[field_name + ":file_field_first_2"] = $("#file_field_" + field + "_first_2").val();
                        form_data[field_name + ":file_field_first_3"] = $("#file_field_" + field + "_first_3").val();

                        form_data[field_name + ":file_field_split"] = $("#file_field_" + field + "_split").val();
                        form_data[field_name + ":file_field_split_splitter"] = $("#file_field_" + field + "_split_splitter").val();
                        form_data[field_name + ":file_field_split_position"] = $("#file_field_" + field + "_split_position").val();
                    }
                };

                console.log(form_data);

                $.ajax({
                    type: "POST",
                    url: window.import_scheme.base_url + "/" +  $(this).attr("data-url"),
                    data: form_data,
                    // contentType: 'application/json',
                    dataType: "json",
                    encode: true,
                    caller: this,
                }).done(function (data) {
                    window.import_scheme.find_item_by_model($(this.caller).attr("data-model")).load();
                });

            });
        };

        // Set dirty to false so it won't rerender if it doesn't need to
        this.dirty = false;
        check_submittable(this.model);
    }

    check_submittable(){
        // Check to see if the form is good to be submitted
        // If it is set the submit button to enabled

        for (let field_id in this.fields){
            let field = this.fields[field_id];

            // Reject if field is blank
            if($("#file_field_" + field).attr("data-is_radio")){
                if($("#file_field_" + field + " input:radio:checked").val() == undefined){
                    return false;
                }
            }

            if($("#file_field_" + field).attr("data-is_dropdown")){
                if($("#file_field_" + field).find(":selected").val() == ""){
                    return false;
                }
            }
            // else{
                if($("#file_field_" + field).find(":selected").val() == ""){
                    return false;
                };

                // Reject if field is "**raw_text**" and "raw_text" input is blank
                if($("#file_field_" + field).find(":selected").val() == "**raw_text**"){
                    if ($("#file_field_" + field + "_raw_text").val() == ""){
                        return false;
                    };
                }; 

                // Reject if field is "**select_first**" and 'select_first' input is blank
                if($("#file_field_" + field).find(":selected").val() == "**select_first**"){
                    let first_count = 0;
                    let first_values = [];

                    for (let count=1; count < 4; i++)
                    {
                        let value = $("#file_field_" + field + "_first_" + count).val();
                        if (value){
                            if (first_values.includes(value)){
                                return false;
                            };
                            first_values.push(value);
                            first_count ++;
                        };
                    };

                    if (first_count < 2){
                        return false;
                    };
                }; 

                // Reject if field is "**split_field**" and '_split_field', '_split_splitter', or '_split_position' input is blank
                if($("#file_field_" + field).find(":selected").val() == "**split_field**"){
                    if (! $("#file_field_" + field + "_split").val() ||
                        ! $("#file_field_" + field + "_split_splitter").val() ||
                        ! $("#file_field_" + field + "_split_position").val()
                    ){
                        return false;
                    };
                }; 
            // };
        };

        // Accept if we get to this point
        return true;
    }
};


function check_submittable(model){
    /// Check to see if the form is good to be submitted

    if (window.import_scheme.find_item_by_model(model).check_submittable()) {
        $("#submit_" + model).removeClass('disabled');
    }
    else {
        $("#submit_" + model).addClass('disabled');
    };
}


function manage_file_field_input(field, model){
    /// Run when selects are updated to show or hide cascading fields

    if($("#file_field_" + field).find(":selected").val() == "**raw_text**"){
        $("#file_field_" + field + "_raw_text").removeClass('not-visible');
    }
    else {
        $("#file_field_" + field + "_raw_text").addClass('not-visible');
    };

    if($("#file_field_" + field).find(":selected").val() == "**select_first**"){
        $("#file_field_" + field + "_first_hider").removeClass('not-visible');
    }
    else {
        $("#file_field_" + field + "_first_hider").addClass('not-visible');
    };

    if($("#file_field_" + field).find(":selected").val() == "**split_field**"){
        $("#file_field_" + field + "_split_hider").removeClass('not-visible');
    }
    else {
        $("#file_field_" + field + "_split_hider").addClass('not-visible');
    };

    check_submittable(model);
};


function prep_upload_progress_bar(args){
    const file_fields = args.file_input_names
    const progress_bar = document.getElementById(args.progress_bar_name);
    const progress_modal = $('#'+args.progress_bar_name+'_modal_control');
    const progress_content = $('#'+args.progress_content);

    $("#"+args.form_name).bind( "submit", function(e) {
        e.preventDefault();
        var formData = new FormData(this);
        
        let file_names = "";
        for (let file_index in file_fields){
            let file = file_fields[file_index];
            file_field = document.getElementById(file).files[0];
            if (file_field != null){
                file_names += file_field.name + "<br>";
            }
        }
        
        progress_content.html(file_names + '<br>');
        progress_modal.modal('show');

        $.ajax({
            type: 'POST',
            url: args.post_url,
            data: formData,
            dataType: 'json',
            beforeSend: function(){
            },
            xhr:function(){
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    if(e.lengthComputable){
                        const percentProgress = (e.loaded/e.total)*100;
                        progress_bar.innerHTML = `<div class="progress-bar progress-bar-striped bg-success" 
                role="progressbar" style="width: ${percentProgress}%" aria-valuenow="${percentProgress}" aria-valuemin="0" 
                aria-valuemax="100"></div>`
                    }
                });
                return xhr
            },
            success: function(response){
                progress_modal.modal('hide');
                window.import_scheme.find_item_by_id(0).load();
            },
            error: function(err){
                console.log(err);
            },
            cache: false,
            contentType: false,
            processData: false,
        });
    });
};


function getCookie(name) {
    /// Django's get cookie function from https://docs.djangoproject.com/en/4.1/howto/csrf/
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// Borrowed from https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
function arraysEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return false;
    if (a.length !== b.length) return false;
  
    // If you don't care about the order of the elements inside
    // the array, you should sort both arrays here.
    // Please note that calling sort on an array will modify that array.
    // you might want to clone your array first.
  
    for (var i = 0; i < a.length; ++i) {
      if (a[i] !== b[i]){
        consol.log("|" + a[i] + "| is different from |" + b[i] + "|");
        return false;
      }
    }
    return true;
  }