import json

from jutsu import Jutsu


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

    jutsu_dict = {
        "rank": {},
        "keywords": set(),
        "list": []
    }

    for line in db:
        line_json = json.loads(line)
        jutsu = Jutsu(line_json)

        # These are Foundry-specific like, folders or something, so skip them
        if jutsu.rank == "CF_tempEntity":
            continue

        if jutsu.rank not in jutsu_dict["rank"].keys():
            jutsu_dict["rank"][jutsu.rank] = []

        jutsu_dict["rank"][jutsu.rank].append(jutsu)
        jutsu_dict["list"].append(jutsu)
        # Insert jutsu keywords into the set
        jutsu_dict["keywords"].update(jutsu.keywords)

    for rank in jutsu_dict["rank"].keys():
        print(f"{rank}-Rank Jutsu: {len(jutsu_dict['rank'][rank])}")

    print(f"Total Jutsu: {len(jutsu_dict['list'])}")
    print()

    # All water jutsu are tagged with "Water Release"
    # Fire is missing 'release' from some

    print(f"Keywords: {' | '.join(jutsu_dict['keywords'])}")

    print(f"Keyword Jutsu Breakdown")
    for keyword in jutsu_dict["keywords"]:
        print(f"{keyword}: {len(filter_keyword(jutsu_dict['list'], keyword))}")


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
