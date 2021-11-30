import optparse
import os
import json

direct_dependencies = {}
all_dependencies = {}


def find_file():
    file_name = ""
    if len(os.getenv("FILE", "")) > 0:
        file_name = os.getenv("FILE", "")
    else:
        files = os.listdir(os.getcwd())
        for file in files:
            if file.endswith(".manifest"):
                file_name = file
                break

    assert len(file_name) != 0
    return file_name


def analyze_file():
    file_name = find_file()

    deps = {}
    with open(file_name, "r") as f:
        lines = f.readlines()
        cur_ab_name = ""
        for line in lines:
            line = line.lstrip()
            if line.startswith("Name:"):
                cur_ab_name = line.split(":")[-1].strip()
                deps[cur_ab_name] = []
            elif line.startswith("Dependency_"):
                dep = line.split(":")[-1].strip()
                deps[cur_ab_name].append(dep)

    return deps


def get_all_dep_by_name(ab_name):
    global direct_dependencies

    direct_deps = direct_dependencies[ab_name]
    if len(direct_deps) == 0:
        return []

    all_deps = []
    for dep in direct_deps:
        all_deps.append(dep)
        deps2 = get_all_dep_by_name(dep)
        for dep2 in deps2:
            if dep2 == dep:
                print(f"ERROR: circular reference found {dep}")
            else:
                all_deps.append(dep2)

    all_deps = list(set(all_deps))
    return all_deps


def write_dependencies():
    global direct_dependencies
    global all_dependencies

    sorted_direct_dependencies = []
    for key in direct_dependencies:
        sorted_direct_dependencies.append({
            "name": key,
            "count": len(direct_dependencies[key]),
            "dependencies": direct_dependencies[key]
        })

    filter_string = os.getenv("FILTER", None)

    sorted_all_dependencies = []
    for key in all_dependencies:
        if filter_string is None or filter_string in key:
            sorted_all_dependencies.append({
                "name": key,
                "count": len(all_dependencies[key]),
                "dependencies": all_dependencies[key]
            })

    sorted_direct_dependencies.sort(key=lambda item: item["count"])
    sorted_direct_dependencies.reverse()

    sorted_all_dependencies.sort(key=lambda item: item["count"])
    sorted_all_dependencies.reverse()

    with open("direct_dependencies.json", "w+") as f:
        f.write(json.dumps(sorted_direct_dependencies, indent=4))

    with open("all_dependencies.json", "w+") as f:
        f.write(json.dumps(sorted_all_dependencies, indent=4))


def main():
    global direct_dependencies
    global all_dependencies

    direct_dependencies = analyze_file()
    all_dependencies = {}
    for ab_name in direct_dependencies:
        all_dependencies[ab_name] = get_all_dep_by_name(ab_name)
        all_dependencies[ab_name].sort()

    write_dependencies()


if __name__ == '__main__':
    usage = "usage:%prog [options] --dirs="
    parser = optparse.OptionParser(usage)
    parser.add_option("-f", "--file", dest="FILE_NAME", help="The manifest file to analyze")
    parser.add_option("-s", "--filter", dest="FILTER", help="string to contain")
    (options, args) = parser.parse_args()
    if options.FILE_NAME:
        os.environ["FILE_NAME"] = options.FILE_NAME
    elif options.FILTER:
        os.environ["FILTER"] = options.FILTER
    main()
