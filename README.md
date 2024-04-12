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

