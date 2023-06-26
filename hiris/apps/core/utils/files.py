import logging, csv
log = logging.getLogger('app')

from ml_export_wizard.utils.exporter import exporters

from hiris.apps.core.utils import db
from hiris.apps.core.models import Feature


def integrations_bed(*, environment: str, title: str=None, file_name: str=None) -> str|None:
    """ Create a bed file based on Integrations, then save it or return it as a string """

    feature = db.get_most_interesting(environment=environment)
    feature_location = feature.feature_locations.all()[0]

    if title:
        title = f"-{title}"

    header: str = "\n".join([
        f'# Position of most "interesting" integrated gene: {feature.feature_name}',
        f"browser position {feature_location.chromosome}:{feature_location.feature_start}-{feature_location.feature_end}",
        "browser hide all",
        "browser full refGene",
        f'browser full "HIRIS{title} - {environment}"',
        f'track name="HIRIS{title} - {environment}" description="HIRIS{title} - {environment} integration sites (blue = F, red = R)" visibility=full colorByStrand="0,0,255 255,0,0" useScore=0 db=hg38 group=genes priority=0\n',
    ])
    body = ""

    query = exporters["IntegrationsSummary"].query(order_by=["landmark", "location"], 
                                                       where=[
                                                                {"field": "integration_environment_name", "value": environment}, 
                                                                {"field": "landmark", "valid": True},
                                                           ]
                                                       )

    #log.debug(query.get_sql())

    for row in query.get_dict_list_generator():
        orientation: str = "+" if row["orientation_in_landmark"] == "F" else ("-" if row["orientation_in_landmark"] == "R" else ".")
        adjusted_row = [row["landmark"], row["location"], row["location"]+1, row["subject_identifier"] or environment, row["multiplicity"], orientation, row["location"], row["location"]]
        body += "\t".join([str(value) for value in adjusted_row]) + "\n"

    if file_name:
        with open(file_name, "w") as f:
            f.write(header + body)
        return

    return header + body
