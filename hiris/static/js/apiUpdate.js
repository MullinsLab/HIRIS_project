function updateAPIEndpoint(args) {
    // push update data to the backend

    if (! (args.keyName && args.keyValue && args.apiEndpoint && args.fields)) {
            throw `Can't update API endpoint without keyName, keyValue and apiEndpoint`;
    }

    console.log("I'mma update something!")
    
    let data = args.fields;
    data[args.keyName] = args.keyValue;

    console.log(data);

    $.ajax({ 
        url: `/api/data_sets/`,
        type: 'PATCH', 
        data: { key: 'value' }, 
        success: function(response) { 
            console.log("Updated");
        }, 
        error: function(xhr, status, error) { 
            console.log("Failed to update");
        } 
    }); 
}