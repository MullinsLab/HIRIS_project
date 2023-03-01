// Variables for the do_import_scheme import_wizard page

class ImportScheme {
    id;                     // ID from the database
    items = [];             // ImportSchemeItem objects
    base_url;               // Base URL for loading from the system
    accordion_container;    // ID of the DOM object being used to hold the accordion
    _this = this;

    constructor(args){
        // Set up the ImportScheme and get it's items
        this.id = args.id;
        this.base_url = args.base_url;
        this.accordion_container = args.accordion_container;

        this.get_items();
    };

    get_items(){
        // Get a list of import_scheme_items 
        $.ajax(this.base_url+'/list', {
            // pass this to caller so it's referrable inside the success function
            caller: this,
            dataType: 'json',
            cache: false,
            success: function(data){
                let items = data.import_scheme_items;
                for (let item in items){
                    this.caller.items.push(new ImportSchemeItem({id: items[item], parent: this.caller}))
                };
            },
        });
    };
};

class ImportSchemeItem{
    id;                     // ID from the database.  Used for loading
    name;                   // Name to be displayed in the accoridon button
    description;            // Description to be displayed in the accordion body - placeholder for HTML form or whatnot
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
            $(this.parent.accordion_container).append(ITEM_TEMPLATE.replaceAll("!ACCORDION_ID!", this.id));

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
        this.body.html(this.description);

        // Set the propper css classes and open/close if item is urgent
        if (this.urgent){
            this.accordion.addClass('border-danger');
            this.button.addClass('accordion-urgent-button');
            this.body.addClass('accordion-urgent');

            this.collapse.collapse('show');
        } else {
            this.accordian.addClass('border-primary');
        };
    }
};

function prep_upload_progress_bar(form_name, file_input_name, progress_bar_name, post_url){
    const input_file = document.getElementById(file_input_name);
    const progress_bar = document.getElementById(progress_bar_name);
    console.log('started script');

    $("#"+form_name).bind( "submit", function(e) {
        console.log('hit form');
        e.preventDefault();
        var formData = new FormData(this);
        const media_data = input_file.files[0];
        if(media_data != null){
            // console.log(media_data);
            progress_bar.classList.remove("not-visible");
        }

        $.ajax({
            type: 'POST',
            url: post_url,
            data: formData,
            dataType: 'json',
            beforeSend: function(){
            },
            xhr:function(){
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    if(e.lengthComputable){
                        const percentProgress = (e.loaded/e.total)*100;
                        // console.log(percentProgress);
                        progress_bar.innerHTML = `<div class="progress-bar progress-bar-striped bg-success" 
                role="progressbar" style="width: ${percentProgress}%" aria-valuenow="${percentProgress}" aria-valuemin="0" 
                aria-valuemax="100"></div>`
                    }
                });
                return xhr
            },
            success: function(response){
                window.location = response.redirect_url;
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