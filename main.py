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

        # These are
        if jutsu.rank == "CF_tempEntity":
            print(line_json)

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

    # keyword_set = OrderedDict()
    # water_jutsu = []
    # for j in jutsu_list:
    #     for k in j.keywords:
    #         keyword_set[k] = 1
    #         if "fire" in k.lower():
    #             water_jutsu.append(j)
    #             break
    #
    print(f"Keywords: {' | '.join(jutsu_dict['keywords'])}")
    # print(f"Filtered Jutsu: {len(water_jutsu)}")


if __name__ == "__main__":
    run()
