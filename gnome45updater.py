#!/usr/bin/env python
import os
import re
import sys
from pprint import pprint



def main(extension_directory: str):
    if not os.path.isdir(extension_directory):
        print(
            f"Provided extension directory is not a valid directory ({extension_directory})"
        )

    source_files = [
        f
        for f in os.listdir(extension_directory)
        if os.path.isfile(os.path.join(extension_directory, f))
        and f.endswith(".js")
        and f != "prefs.js"
    ]

    user_messages = {}

    # Get and remap imports with regex
    pattern = r"(?P<decleration_type>(const)|(let)|(var))\s+(?P<var_names>[{]?[\w\s,]+[}]?)\s+(?P<import_path_full>=\s+(?P<local_import>Me.)?imports.(?P<import_path>[\w.]+))(?P<function>\(.+)?"

    changed_imports = {}

    for file_name in source_files:
        changed_imports[file_name] = []
        with open(os.path.join(extension_directory, file_name)) as f:
            file_contents = f.read()
            new_file_contents = file_contents
            matches: list[re.Match] = list(re.finditer(pattern, file_contents))
            print("\n  |$>", file_name)
            for match in matches:
                spos, epos = match.span()
                match_groups: dict[str, str] = match.groupdict()
                new_import_target = None
                old_import_target = file_contents[spos:epos]

                var_names = (
                    match_groups["var_names"]
                    .replace("{", "")
                    .replace("}", "")
                    .strip()
                    .split(",")
                )
                if match_groups["local_import"]:
                    new_import_target = (
                        f"import * as {var_names[0]} from './{var_names[0]}.js';"
                    )
                elif match_groups["function"]:
                    fn = match_groups["function"]
                    if "getCurrentExtension" in match_groups["import_path"]:
                        new_import_target = "import * as Me from './extension.js';"
                    elif "gettext.domain" in match_groups["import_path"]:
                        new_import_target = ""
                        user_messages["Please set the `gettext-domain` key in `metadata.json`"] = True
                    else:
                        print("Unhandled Function Import", match, match_groups)
                elif match_groups["import_path"] == "gi":
                    version_pattern = r"(?P<import_path_full>imports.(?P<import_path>[\w.]+))\s+=\s+?['|\"](?P<version_number>[\d.]+)['|\"]"
                    version_matches: list[re.Match] = list(re.finditer(version_pattern, file_contents))

                    new_import_target = ""
                    for var_name in var_names:
                        var_name = var_name.strip()

                        version = ""
                        for version_match in version_matches:
                            version_match_groups = version_match.groupdict()
                            lib_name = version_match_groups["import_path"].split(".")[-1]
                            if lib_name.strip() == var_name:
                                version = version_match_groups["version_number"]

                        new_import_target += (
                            old_import_target.replace(
                                match_groups["var_names"], var_name
                            )
                            .replace(
                                match_groups["import_path_full"],
                                f"from 'gi://{var_name}{f'?version={version}' if version else ''}';",
                            )
                            .replace(match_groups["decleration_type"], "import")
                            + "\n"
                        )
                else:
                    import_path_parts = match_groups["import_path"].split(".")
                    new_import_target = "/".join(import_path_parts) + ".js"
                    new_import_target = new_import_target.strip()
                    new_import_target = (
                        old_import_target.replace(
                            match_groups["import_path_full"],
                            f"from 'resource:///org/gnome/shell/{new_import_target}';",
                        )
                        .replace(match_groups["decleration_type"], "import")
                        .replace(" Main", " * as Main")
                        .replace(" Util", " * as Util")
                    )

                if new_import_target is None:
                    print("Unhandled import", match, match_groups)
                else:
                    new_import_target = new_import_target.strip()
                    changed_imports[file_name].append((match, old_import_target, new_import_target,))



                new_file_contents = file_contents[:spos] + new_import_target + file_contents[epos:]
                # print(new_file_contents)

                import_changes = changed_imports[file_name]
                for change in import_changes:
                    m, old, new = change
                    print(m)
                    print("OLD:", old)
                    print("NEW:", new)
                    print()
    all_import_changes = sum([imports for imports in list(changed_imports.values())], [])
    # pprint(all_import_changes)
    print(len(all_import_changes), "imports updated in", len(changed_imports), "of", len(source_files), "files")
    print(list(user_messages.keys()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please provide the extension directory as the first console argument")
    else:
        main(sys.argv[1])
