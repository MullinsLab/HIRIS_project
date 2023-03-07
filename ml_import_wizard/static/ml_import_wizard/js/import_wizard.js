// Variables for the do_import_scheme import_wizard page

class ImportScheme {
    id;                     // ID from the database
    items = [];             // ImportSchemeItem objects
    base_url;               // Base URL for loading from the system
    accordion_container;    // ID of the DOM object being used to hold the accordion
    _this = this;

    constructor(args){
        // Set up the ImportScheme and get its items
        this.id = args.id;
        this.base_url = args.base_url;
        this.accordion_container = args.accordion_container;

        this.get_items();
    };

    find_item_by_id(id){
        return this.items.find(item => item.id == id);
    };

    get_items(){
        // Get a list of import_scheme_items from the backend
        $.ajax(this.base_url+'/list', {
            // pass this to caller so it's referrable inside the success function
            caller: this,
            dataType: 'json',
            cache: false,
            success: function(data){
                let items = data.import_scheme_items;
                for (let item in items){
                    this.caller.items.push(new ImportSchemeItem({id: items[item], index: this.caller.items.length, parent: this.caller}))
                    
                    // Set up a base_accordion_X as a placeholder for the accordion block
                    $(this.caller.accordion_container).append("<div id='base_accordion_" + (this.caller.items.length-1) + "'>");
                };
            },
        });
    };
};

class ImportSchemeItem{
    id;                     // ID from the database.  Used for loading
    index;                  // Index number of the list of items from the parent
    name;                   // Name to be displayed in the accoridon button
    description;            // Description to be displayed in the accordion body - placeholder for HTML form or whatnot
    form;                   // The form to use to collect informatoin about this item
    urgent = false;         // Is the Item urgent, meaning that it needs to be dealt with before the import can happen
    start_expanded;         // If true, the accordion will start in an expanded state
    dirty;                  // Indicates that the item is dirty and needs to be rerendered
    parent;                 // ImportScheme this Item belongs to
    
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
        $.ajax(this.parent.base_url+'/'+this.id, {
            // pass this to caller so it's referrable inside the success function
            caller: this,
            dataType: 'json',
            cache: false,
            success: function(data){
                this.caller.set_with_dirty({field: 'name', value: data.name});
                this.caller.set_with_dirty({field: 'description', value: data.description});
                this.caller.set_with_dirty({field: 'form', value: data.form});
                this.caller.set_with_dirty({field: 'urgent', value: data.urgent});
                this.caller.set_with_dirty({field: 'start_expanded', value: data.start_expanded});

                this.caller.render();
            },
        });
    };

    set_with_dirty(args){
        // Sets the field value if different from current, and if so sets dirty to true
        if (this[args.field] != args.value){
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

        let body_bit = this.description;
        if (this.form){body_bit += '<br><br>'+this.form}
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

        // Set dirty to false so it won't rerender if it doesn't need to
        this.dirty = false;
    }
};

function prep_upload_progress_bar(args){
    const input_file = document.getElementById(args.file_input_name);
    const progress_bar = document.getElementById(args.progress_bar_name);
    // const progress_modal = document.getElementById(args.progress_bar_name+'_modal_control');

    // const input_file = $('#'+args.file_input_name);
    // const progress_bar = $('#'+args.progress_bar_name);
    const progress_modal = $('#'+args.progress_bar_name+'_modal_control');
    const progress_content = $('#'+args.progress_content);
    console.log('started script');

    $("#"+args.form_name).bind( "submit", function(e) {
        console.log('hit form');
        e.preventDefault();
        var formData = new FormData(this);
        const media_data = input_file.files[0];
        if(media_data != null){
            console.log(media_data);
            progress_content.html(media_data.name+'<br><br>')
            progress_modal.modal('show');
        }
        
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
                // window.location = response.redirect_url;
                console.log('Saved file');
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