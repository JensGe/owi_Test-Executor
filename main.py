from systems import websch, database, compute, aws
from common import enum, pyd_models as pyd
from time import sleep
import json

example_db_settings = dict(
    fqdn_amount=1000,
    min_url_amount=5,
    max_url_amount=5,
    visited_ratio=None,
    connection_amount=None
    )

repetition = 10

case_settings = pyd.CaseSettings(
    logging_mode=None,
    crawling_speed_factor=None,
    default_crawl_delay=None,
    parallel_process=[1, 2, 4, 8, 16, 32, 64],
    iterations=[1],
    fqdn_amount=[10],
    url_amount=None,
    long_term_mode=[enum.LTF.large_sites_first, enum.LTF.small_sites_first],
    short_term_mode=None,
    min_links_per_page=[2],
    max_links_per_page=[2],
    lpp_distribution_type=None,
    internal_vs_external_threshold=[1.0],
    new_vs_existing_threshold=[1.0],
)


def main():
    print("Reset Example DB ...")
    websch.delete_example_db()
    websch.generate_example_db(**example_db_settings)

    print("Backup FQDN- & URL-Frontier Tables ...")
    database.backup_table("fqdn_frontiers")
    database.backup_table("url_frontiers")

    print("Compute Cases ...")
    settings_collection = compute.create_cases(case_settings, repetition)
    print("Cases created: {}".format(len(settings_collection)))

    for setting in settings_collection:
        print("* Reset Example DB ...")
        websch.delete_example_db()
        database.restore_table("fqdn_frontiers")
        database.restore_table("url_frontiers")

        print("* Set Fetcher Settings ...")
        print("* Case {}".format(setting))
        websch.set_fetcher_settings(setting)

        print("* Create EC2 Instance ...")
        instance_id = aws.create_instance()
        file_name = instance_id + ".log"

        file_found = False
        print("* Waiting for {}.log-File in S3 Bucket ...".format(instance_id))
        while not file_found:
            print("-", end="")
            sleep(30)
            file_found = aws.download_file(file_name)

        print("* Terminate EC2 Instance ...")
        aws.terminate_instance(instance_id)

    with open("fetsim-logs/results.json", "w") as file:
        json.dump(compute.jsonify_results(), file)



if __name__ == "__main__":
    main()
