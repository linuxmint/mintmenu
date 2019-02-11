#!/usr/bin/python3

import sys

import apt_pkg

if len(sys.argv) != 2:
    sys.exit(1)
try:
    apt_pkg.init()
    cache = apt_pkg.Cache()
    package_records = apt_pkg.PackageRecords(cache)
    known_packages = set()
    with open(sys.argv[1], "w") as f:
        for pkg in cache.packages:
            if pkg.selected_state or not pkg.version_list or pkg.name in known_packages:
                continue
            name = pkg.name
            package_records.lookup(pkg.version_list.pop(0).translated_description.file_list.pop(0))
            summary = package_records.short_desc
            description = package_records.long_desc.replace(summary + "\n ", "").replace("\n .\n ", "~~~").replace("\n", "")
            f.write("CACHE###%s###%s###%s\n" % (name, summary, description))
            known_packages.add(name)
except Exception as e:
    print("ERROR###ERROR###ERROR###ERROR")
    print(e)
    sys.exit(1)
