if (!window.ISDB)         window.ISDB = {};
if (!window.ISDB.Exports) window.ISDB.Exports = {};
window.ISDB.Exports["summary-by-gene"] =
[
{% for gene in summary %}
    {"environment":{% if gene.integration_environment_name %}"{{ gene.integration_environment_name }}"{% else %}null{% endif %},
    "gene":{% if gene.feature_name %}"{{ gene.feature_name }}"{% else %}null{% endif %},
    "gene_type":{% if gene.gene_type_name %}"{{ gene.gene_type_name }}"{% else %}null{% endif %},
    "ncbi_gene_id":1,
    "proliferating_sites":{{ gene.proliferating_sites|default_if_none:"null" }},
    "subjects":{{ gene.subjects|default_if_none:"null" }},
    "total_in_gene":{{ gene.total_in_gene|default_if_none:"null" }},
    "unique_sites":{{ gene.unique_sites|default_if_none:"null" }}}
{% if not forloop.last%},{% endif %}
{% endfor for %}
]