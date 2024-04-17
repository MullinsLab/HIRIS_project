# HIRIS_project
HIV-1 Reservoirs Integration Sites 

---

### Instalation

Clone GitHub repository  
Copy .env.TEMPLATE to .env  
Generate a secret key and put into .env  
update docker-compose.yml lines 11 and 31 to change the PostgreSQL password from mypassword to something more secure.  The password must match in both places  

### Initial loading of genome data
Add ref_GRCh38.p2_top_level.gff3
Add Homo_sapiens.gene_info_modified.tsv
Add chr_accessions_GRCh38_modified.tsv

Set ref_GRCh38.p2_top_level.gff3 as primary

Link ref_GRCh38.p2_top_level.gff3 -> Dbxref with 
* Homo_sapiens.gene_info_modified.tsv -> GeneID

Link ref_GRCh38.p2_top_level.gff3 -> seqid with
* chr_accessions_GRCh38_modified.tsv -> RefSeq Accession.version

Specify:
* Genome Species = Homo Sapiens
* Genome Version = GRCh38.p2

Set up import fields:
* Gene Type
    * Gene Type Name = Homo_sapiens.gene_info_modified.tsv -> type_of_gene

* Feature Type
    * Feature Type Name = ref_GRCh38.p2_top_level.gff3 -> featuretype

* Feature
    * Feature Name = ref_GRCh38.p2_top_level.gff3 -> Name
    * External Gene ID = Split Field, Homo_sapiens.gene_info_modified.tsv -> GeneID, Using Character -> :, keeping  value in position -> 2

* Feature Location
    * Chromosome = chr_accessions_GRCh38_modified.tsv -> Chromosome
    * Landmark = ref_GRCh38.p2_top_level.gff3 -> seqid
    * Feature Start = ref_GRCh38.p2_top_level.gff3 -> start
    * Feature End = ref_GRCh38.p2_top_level.gff3 -> end
    * Feature Orientation = ref_GRCh38.p2_top_level.gff3 -> strand

### Intial loading of previous ISDB data
Add ISDB_Data.csv

Set up import fields:
* Genome Version
    * Genome Version Name: Select "GRCh38.p2" under "Values from Genome Version Name"

* Data Set
    * Data Set Name: data_set_name

* Publication
    * Publication Pubmed ID: publication_pubmed_id

* Data Set Source
    * Document Pubmed ID: document_pubmed_id
    * Document Uri: document_uri

* Subject
    * Subject Identifier: subject_identifier

* Subject Data
    * Click "Unused"

* Sample
    *Sample Name: Set to "No Data"

* Sample Data
    * date
        * Select "culture" from drop down
        * Click "Add"
        * Select "culture" from dropdown in Key column
    * Repeat for
        * culture_day
        * date
        * disease
        * genbank
        * original_id
        * provirus_activity
        * pubmed_id
        * replicates
        * tissue
        * tissue_url
        * type
        * visit
        * years_on_art

* Preparation
    * Preparation Description: preparation_description

* Sequencing Method
    * Sequencing Method Name: Set to "No Data"
    * Sequencing Method Description: Set to "No Data"

* Integration Environment
    * Integration Environment Name: integration_environment_name

* Integration
    * Integration Name: Set to "No Data"
    * Ltr: ltr
    * Multiple Integration: Set to "No Data"
    * Multiple Integration Count: Set to "No Data"
    * Sequence: sequence
    * Junction 5P: junction_5p
    * Junction 3P: Set to "No Data"
    * Sequence Name: sequence_name
    * Sequence Uri: sequence_uri
    * Ltr Sequence: Set to "No Data"
    * Breakpoint Sequence: Set to "No Data"
    * Umi Sequence: Set to "No Data"
    * Ltr Sequence 5P: Set to "No Data"
    * Breakpoint Sequence 5P: Set to "No Data"
    * Umi Sequence 5P: Set to "No Data"
    * Ltr Sequence 3p: Set to "No Data"
    * Breakpoint Sequence 3p: Set to "No Data"
    * Umi Sequence 3P: Set to "No Data"
    * Provirus Sequence: Set to "No Data"
    * Replicate: Set to "No Data"
    * Replicates: Set to "No Data"
    * Note: note

* Integration Location
    * Landmark: "Translate Chromosome To Ascession ID" Chromosome: landmark
    * Location: location
    * Breakpoint Landmark: Set to "No Data"
    * Breakpoint Location: Set to "No Data"
    * Landmark 5P: Set to "No Data"
    * Location 5P: Set to "No Data"
    * Breakpoint Landmark 5P: Set to "No Data"
    * Breakpoint Location 5P: Set to "No Data"
    * Landmark 3P: Set to "No Data"
    * Location 3p: Set to "No Data"
    * Breakpoint Landmark 3P: Set to "No Data"
    * Breakpoint Location 3P: Set to "No Data"
    * Orientation In Landmark: orientation_in_landmark

* Blast Info
    * Identity: identity
    * Q Start: q_start
    * Gaps: gaps
    * Score: Set to "No Data"

Run management command "process_after_import"
```root@b7b166e095bd:/hiris# ./manage.py process_after_import```