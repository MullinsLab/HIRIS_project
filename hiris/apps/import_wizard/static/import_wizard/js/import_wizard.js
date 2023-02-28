// Variables for the do_import_scheme import_wizard page

class ImportScheme {
    id;                     // ID from the database
    items = [];             // ImportSchemeItem objects
    base_url;               // Base URL for loading from the system
    accordion_id;           // ID of the DOM object being used for the accordion
    _this = this;

    constructor(args){
        // Set up the ImportScheme and get it's items
        this.id = args.id;
        this.base_url = args.base_url;
        this.accordion_id = args.accordion_id;

        this.get_items();
        console.log("Items: " + this.items);
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
                    console.log("Item: " + item + ", Value:" + items[item])
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
    parent;                 // ImportScheme this Item belongs to

    constructor(args){
        console.log('Creating an object!')
        this.id = args.id;
        this.parent = args.parent;

        console.log(this.parent);

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
                this.caller.name = data.name;
                this.caller.description = data.description;
                this.caller.urgent = data.urgent;
                this.caller.start_expanded = data.start_expanded;

                console.log(this.caller);
            },
        });
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