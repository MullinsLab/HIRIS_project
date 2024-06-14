function updateAPIEndpoint(args) {
    // push update data to the backend

    if (! (args.keyValue && args.apiEndpoint && args.fields)) {
            throw `Can't update API endpoint without keyName, keyValue and apiEndpoint`;
    }

    console.log(args.fields)

    $.ajax({ 
        url: `/api/${args.apiEndpoint}/${args.keyValue}/`,
        method: 'PATCH', 
        headers: {'X-CSRFToken': csrftoken},
        mode: 'same-origin',
        data: args.fields, 
        success: function(response) { 
            // Add in when needed
        }, 
        error: function(xhr, status, error) { 
            console.log("Failed to update");
        } 
    }); 
}


