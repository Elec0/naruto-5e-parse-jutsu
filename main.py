import json

from common import JutsuRankException
from jutsu import Jutsu
from jutsu_db import JutsuDB


# "name"
# "system": {
#   "description": { "value" }
#   "activation": {
#        "type", "cost", "condition"
#        type is things like: "action", "bonus", "reaction", "minute/hour/day"
#        cost is usually "1", but can be "0", or other numbers for minutes/hours/days
#        condition is things like: "full round action, when you would take damage, must be in a stance"
# }
# }


def run():
    with open("jutsu.db", encoding="utf-8") as f:
        db = f.readlines()

    jutsu_db = JutsuDB()

    for line in db:
        line_json = json.loads(line)
        try:
            jutsu = Jutsu(line_json)
        except JutsuRankException as ex:
            continue

        # These are Foundry-specific like, folders or something, so skip them
        if jutsu.rank == "CF_tempEntity":
            continue

        jutsu_db.add(jutsu)

    # Assemble some stats for the jutsu
    for rank in jutsu_db.rank.keys():
        print(f"{rank}-Rank Jutsu: {len(jutsu_db.rank[rank])}")

    print(f"Total Jutsu: {len(jutsu_db.all_jutsu)}")
    print()

    print(f"Keywords: {' | '.join(jutsu_db.all_keywords)}")
    print()

    print(f"Keyword Jutsu Breakdown")
    for keyword in sorted(list(jutsu_db.all_keywords)):
        print(f"{keyword}: {len(filter_keyword(jutsu_db.all_jutsu, keyword))}")

    print(jutsu_db.get("Chakra Movement").to_yaml())


def filter_keyword(jutsu_list: list[Jutsu], keyword: str) -> list[Jutsu]:
    """
    Filter a list of jutsu by a keyword
    :param jutsu_list:
    :param keyword: What substring to search for
    :return: A list of jutsu that contain the keyword
    """
    filtered_list = []
    for j in jutsu_list:
        for k in j.keywords:
            if keyword.lower() in k.lower():
                filtered_list.append(j)
                break

    return filtered_list


if __name__ == "__main__":
    run()
