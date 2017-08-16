"""
This file would be used to parser merge diff files of github
Identification of a hunk:
Every hunk starts in the following way:
@@@ ... @@@
So the first thing we need to recognise is this.

"""


class Parser:

    def __init__(self, diff):
        """
        initialize Parser
        :param diff: diff
        """
        self.diff = diff.split("\n")
        self.hunk_identifier = "@@@"
        self.file_identifier = "diff"

    def get_hunks(self, file):
        """
        returns the hunks as a list

        :param file: file is a string here
        :return:
        """
        hunks = []
        hunk = ""
        file = file.file
        for line in file:
            if line[:3] == self.hunk_identifier:
                hunks.append(Hunk(hunk))
                hunk = ""
                hunk += line + "\n"
            else:
                hunk += line + "\n"

        hunks.append(Hunk(hunk))

        hunks.pop(0)
        return hunks

    def get_files(self):
        """
        returns all files in the diff

        :return:
        """
        files = []
        changed_file = ""
        for line in self.diff:
            if line[:4] == self.file_identifier:
                files.append(File(changed_file))
                changed_file = ""
                changed_file += line + "\n"
            else:
                changed_file += line + "\n"

        files.append(File(changed_file))

        files.pop(0)
        # returns a list of objects of custom type File
        return files


class File:

    def __init__(self, file):
        """
        initialization

        :param file: file is of type string
        """
        self.file = file.split("\n")
        self.filename = self.get_filename()

    def __str__(self):
        """
        string representation

        :return:
        """
        string_representation = ""
        for line in self.file:
            string_representation += line + "\n"
        return string_representation


    def get_filename(self):
        """
        return the filename

        :return:
        """
        return self.file[0].split(" ")[-1]


class Hunk:

    def __init__(self, hunk):
        """
        initialization

        :param hunk: hunk is a string
        """
        self.hunk = hunk.split("\n")
        self.base_identifier_start = "++<"
        self.base_identifier_end = "++="
        self.head_identifier_start = "++="
        self.head_identifier_end = "++>"
        self.added_lines_base = self.get_added_lines_base()
        self.added_lines_head = self.get_added_lines_head()

    def __str__(self):
        """
        string representation

        :return:
        """
        string_representation = ""
        for line in self.hunk:
            string_representation += line + "\n"
        return string_representation

    def get_added_lines_base(self):
        """
        returns the lines added for the base, the current

        :return:
        """
        added_lines = set()
        flag = 0
        for line in self.hunk:
            if flag == 1:
                added_lines.add(line)
            if line[:3] == self.base_identifier_start:
                flag = 1
            elif line[:3] == self.base_identifier_end:
                break

        return added_lines

    def get_added_lines_head(self):
        """
        returns the lines added for the head, the incoming

        :return:
        """
        added_lines = set()
        flag = 0
        for line in self.hunk:
            if flag == 1:
                added_lines.add(line)
            if line[:3] == self.head_identifier_start:
                flag = 1
            elif line[:3] == self.head_identifier_end:
                break

        return added_lines

    def remove_preceeding_plus_character(self, line):
        """
        removes the preceeding + sign in lines which are added
        :param line:
        :return:
        """
