# ToDo:

```
Work out user permissions
Update data structures to support user permissions
Update data structures to support freezing
DB Problems
    All views are very slow
    Integration_Genes is especially slow.  Have a link directly from 
Add freeze table
    Duplicate data used in the freeze
    or version data instead?
Work out what's stored in the JSON fields
    Pull data out of JSON fields?
Set up tests
```

# Notes on DB Reorg:

Round 1
Renamed Integration to Integrations, Source to Sources, NCGI\_Gene to NCGI\_Genes, and NCGI\_Gene\_Location to NCGI\_Gene\_Locations.
Normalized Sources into one table.
Added ID fields to each table that didn't have them.
Made an explicit link from Integrations to NCGI\_Gene\_Locations so it doesn't have to do expensive comparisons each time.
Added Integration\_Sample and Integration\_Info tables to get the JSON fields out of Integration and keep it managable for people writing queries.
 It doesn't look like we need to accommodate arbitrary field/value pairs in Sample, but if we do this can be changed to allow for it.
 These fields aren't in any particular order. If there is an order that would make better sense it can be changed.
 Pubmed\_ID shows up both in Source and Integration. Probably should just be in Source?
 If some of the fields aren't needed they can be removed
 Are Replicate and Replicates the same data with different names?
 Are Source\_File and Sources.Data\_Path the same information? They are structured differently.
Added Genome\_Version table
Added Data\_Sets table
 Data Sets refer to what have been Frozen databases
 Each Data Set links to one version of the Genome. If the data is needed in a Data Set linked to a different version it will need to be coppied and updated to match the new version.
 If there is a better name than Data Set it can be updated.

Round 2
Moved NCGI_Gene to Gene.  If the genes are from a different organism it may not be coming from the NCGI
    Added External_ID to replace NCGI_Gene_ID.  This field is named in the Genomes.External_Gene_ID_Name field.
        Example: If the gene is from NCGI, the External_Gene_ID_Name would be NCGI_Gene_ID and any export of the data would have the column labeled that.
Linked Genome to Gene table
Added Dates to Genomes, Sources, Data Sets.  This may never be needed, but it's cheap and it gives some history to the data, if it's ever needed.

# Questions:

Are there times that a HIRIS data set would be frozen other than to align it with a different version of the Human Genome? 
**Yes, when new data has been added and an analysis is about to begin on the revised dataset.**

At the last meeting Jim mentioned integration with TCozy.  Is that pulling data from TCozy or pushing data to it, or generating integrated reports or data sets, or something else?
**I think that TCozy sends data (I don’t think it is an automated push) to ISDB**

HIRIS is a data source for Redash.  Is that something that people use?  Are there likely to be stored queries in Redash that we need to ensure continue to work with the new HIRIS implementation?
**Redash is definitely helpful on occasion and should be maintained since a publication might need an older version to be cited somehow, perhaps on github. I expect that new redash queries might emerge once the db is up an running and new data is added.**
