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
    ]

    user_messages = {}

    extension_class_name = extension_directory.split("@")[0].capitalize()

    # Get and remap imports with regex
    pattern = r"(?P<decleration_type>(const)|(let)|(var))\s+(?P<var_names>[{]?[\w\s,]+[}]?)\s+(?P<import_path_full>=\s+(?P<local_import>Me.)?imports.(?P<import_path>[\w.]+))(?P<function>\(.+)?"

    changed_imports = {}

    for file_name in source_files:
        print("\n  |$>", file_name)
        changed_imports[file_name] = []
        with open(os.path.join(extension_directory, file_name)) as f:
            file_contents = f.read()
            new_file_contents = file_contents


            # Update the extension.js functions into
            if file_name == "prefs.js":
                user_messages[
                    "Please manually updated `prefs.js`"
                ] = True
                continue

            if file_name == "extension.js":
                extension_pattern = r"function\s*([A-z0-9]+)?\s*\((?:[^)(]+|\((?:[^)(]+|\([^)(]*\))*\))*\)\s*\{(?:[^}{]+|\{(?:[^}{]+|\{[^}{]*\})*\})*\}"
                ext_matches = list(
                    re.finditer(extension_pattern, file_contents, flags=re.MULTILINE)
                )




                new_class_contents = "import { Extension, gettext as _ } from 'resource:///org/gnome/shell/extensions/extension.js';\n\n"
                new_class_contents += (
                    f"export default class {extension_class_name} extends Extension {{\n\n"
                )
                new_class_contents += (
                    "\n\n".join(
                        [em.string[em.start() : em.end()] for em in ext_matches]
                    )
                    + "\n\n}\n"
                )

                s, e = ext_matches[-1].span()
                new_file_contents = new_file_contents[:s] + new_file_contents[e:]
                s, e = ext_matches[0].span()
                new_file_contents = new_file_contents[:s] + new_class_contents + new_file_contents[e:]
                # print(new_file_contents)

            matches: list[re.Match] = list(re.finditer(pattern, new_file_contents))
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
                        new_import_target = f"import * as MeModule from './extension.js'; \nconst Me = MeModule.{extension_class_name};"
                    elif "gettext.domain" in match_groups["import_path"]:
                        new_import_target = "import { Extension, gettext as _ } from 'resource:///org/gnome/shell/extensions/extension.js';"
                        user_messages[
                            "Please set the `gettext-domain` key in `metadata.json`"
                        ] = True
                    else:
                        print("Unhandled Function Import", match, match_groups)
                elif match_groups["import_path"] == "gi":
                    version_pattern = r"(?P<import_path_full>imports.(?P<import_path>[\w.]+))\s+=\s+?['|\"](?P<version_number>[\d.]+)['|\"]"
                    version_matches: list[re.Match] = list(
                        re.finditer(version_pattern, file_contents)
                    )

                    new_import_target = ""
                    for var_name in var_names:
                        var_name = var_name.strip()

                        version = ""
                        for version_match in version_matches:
                            version_match_groups = version_match.groupdict()
                            lib_name = version_match_groups["import_path"].split(".")[
                                -1
                            ]
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
                    changed_imports[file_name].append(
                        (
                            match,
                            old_import_target,
                            new_import_target,
                        )
                    )

                new_file_contents = (
                    file_contents[:spos] + new_import_target + file_contents[epos:]
                )
                # print(new_file_contents)

                import_changes = changed_imports[file_name]
                for change in import_changes:
                    m, old, new = change
                    print(m)
                    print("OLD:", old)
                    print("NEW:", new)
                    print()
    all_import_changes = sum(
        [imports for imports in list(changed_imports.values())], []
    )
    # pprint(all_import_changes)
    print(
        len(all_import_changes),
        "imports updated in",
        len([c for filename, c in changed_imports.items() if len(c) > 0]),
        "of",
        len(source_files),
        "files",

    )
    print(list(user_messages.keys()))

        # TODO: extensionUtils.getSettings to Extension.getSettings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please provide the extension directory as the first console argument")
    else:
        main(sys.argv[1])
