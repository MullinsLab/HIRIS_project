import logging, csv

log = logging.getLogger("app")

from ml_export_wizard.utils.exporter import exporters, ExporterQuery

from hiris.apps.core.utils import db
from hiris.apps.core.models import Feature, FeatureLocation
from hiris.apps.core.utils.simple import dict_hash


def integrations_bed(
    *, environment: str, title: str = None, file_name: str = None
) -> str | None:
    """Create a bed file based on Integrations, then save it or return it as a string"""

    feature: Feature = db.get_most_interesting(environment=environment)
    feature_location: FeatureLocation = feature.feature_locations.all()[0]

    if title:
        title = f"-{title}"

    header: str = "\n".join(
        [
            f'# Position of most "interesting" integrated gene: {feature.feature_name}',
            f"browser position {feature_location.chromosome}:{feature_location.feature_start}-{feature_location.feature_end}",
            "browser hide all",
            "browser full refGene",
            f'browser full "HIRIS{title} - {environment}"',
            f'track name="HIRIS{title} - {environment}" description="HIRIS{title} - {environment} integration sites (blue = F, red = R)" visibility=full colorByStrand="0,0,255 255,0,0" useScore=0 db=hg38 group=genes priority=0\n',
        ]
    )

    body: str = ""

    query: ExporterQuery = exporters["IntegrationsSummary"].query(
        order_by=["landmark", "location"],
        where=[
            {"field": "integration_environment_name", "value": environment},
            {"field": "landmark", "valid": True},
        ],
    )

    for row in query.get_dict_list_generator():
        if chromosome := db.get_chromosome_from_landmark(
            landmark=row["landmark"], genome_version=row["genome_version_name"]
        ):
            orientation: str = (
                "+"
                if row["orientation_in_landmark"] == "F"
                else ("-" if row["orientation_in_landmark"] == "R" else ".")
            )
            adjusted_row: list = [
                chromosome,
                row["location"],
                row["location"] + 1,
                row["subject_identifier"] or environment,
                row["multiplicity"],
                orientation,
                row["location"],
                row["location"],
            ]

            body += "\t".join([str(value) for value in adjusted_row]) + "\n"

    if file_name:
        with open(file_name, "w") as f:
            f.write(header + body)
        return

    return header + body


def integration_gene_summary_gff3(
    *, gene: str = None, file_name: str = None
) -> str | None:
    """Create a gff3 file based on IntegrationsGeneSummary then return it as a string or save it"""

    header: str = "\n".join(
        [
            "##gff-version 3",
            "#seqid	source	type	start	end	score	strand	phase	attributes",
        ]
    )
    body: str = ""

    if gene:
        query: ExporterQuery = exporters["IntegrationsGeneSummary"].query(
            where=[{"field": "feature_name", "value": gene}]
        )
    else:
        query: ExporterQuery = exporters["IntegrationsGeneSummary"].query(
            where=[{"field": "feature_name", "valid": True}]
        )

    query.order_by = ["feature_name", "location"]

    log.debug(query.where)

    for row in query.get_dict_list_generator():
        orientation: str = (
            "+"
            if row["orientation_in_landmark"] == "F"
            else ("-" if row["orientation_in_landmark"] == "R" else ".")
        )
        location: int = (
            row["location"] - row["feature_start"] + 1
        )  # Add 1 to the start position to make it 1-based

        adjusted_row: list = [
            f"{row['feature_name']} - {row['external_gene_id']}",
            row["source_names"],
            "proviral_location",
            location,
            location,
            row["multiplicity"],
            orientation,
            ".",
        ]

        attributes: str = ""
        attributes += f"ID={dict_hash(dictionary=row)}"
        attributes += (
            f";Name={row['subject_identifier'] or row['integration_environment_name']}"
        )

        adjusted_row.append(attributes)

        body += "\n" + "\t".join([str(value) for value in adjusted_row])

    if file_name:
        with open(file_name, "w") as f:
            f.write(header + body)
        return

    return header + body
