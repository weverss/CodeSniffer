import sublime
import sublime_plugin

import os
import re
import sys
import subprocess
import xml.etree.ElementTree as etree


class CodeSniffer(sublime_plugin.TextCommand):

    def run(self, view):

        # Load settings
        self.settings = sublime.load_settings("CodeSniffer.sublime-settings")
        self.local_working_copy = self.settings.get("local_working_copy")
        self.remote_working_copy = self.settings.get("remote_working_copy")
        self.vm_host = self.settings.get("vm_host")
        self.vm_user = self.settings.get("vm_user")
        self.svn_repositories = self.settings.get("svn_repositories", [])

        self.view.window().run_command(
            "show_panel", {
                "panel": "console",
                "toggle": False
            }
        )

        print("\n" * 100)
        print("[Code Sniffer]")

        uncommitted_changed_files = self.get_uncommitted_changed_files()

        for uncommitted_changed_file in uncommitted_changed_files:
            output = subprocess.check_output([
                "ssh",
                "%s" % "{0}@{1}".format(self.vm_user, self.vm_host),
                "code-sniffer.sh " + uncommitted_changed_file
            ])

            print(output.decode())

    def get_uncommitted_changed_files(self):
        files = []

        for repository in self.svn_repositories:
            working_copy = self.local_working_copy + "/" + repository

            svn_output = subprocess.check_output(
                ['svn', 'status', working_copy, '--xml']
            )

            files = files + self.extract_files_from_shell_output(svn_output)

        return files

    def extract_files_from_shell_output(self, output):
        files = []

        output = output.decode()
        root = etree.fromstring(output)

        for child in root.iter("entry"):
            file_path = child.attrib["path"]

            if not file_path.startswith(self.local_working_copy):
                continue

            if not file_path.endswith('.php'):
                continue

            if not os.path.isfile(file_path):
                continue

            file_path = file_path.replace(
                self.local_working_copy,
                self.remote_working_copy
            )

            files.append(re.escape(file_path))

        return files
