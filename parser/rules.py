#!/usr/bin/env python3

import sys
import yaml
import re


class DuplicateUUID(Exception):
    pass


class GlobalUuid:
    def __init__(self):
        self._map = {}

    def _valid_uuid(self, uuid):
        Reg = r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
        if not re.match(Reg, uuid):
            return False

        return True

    def validate(self, uuid):
        # Each UUID must be unknown
        try:
            self._map[uuid]
        except KeyError:
            self._map[uuid] = True
            return self._valid_uuid(uuid)

        return False


class Pattern:
    def __init__(self, P, UuidStore):
        uuid = None
        triggers = None
        map = None
        ptn = None
        type = None
        name = None
        partition = None

        try:
            uuid = P["id"]
        except KeyError:
            raise ValueError(f"Pattern {P}  does not have an id")

        if not UuidStore.validate(uuid):
            raise ValueError(f"Pattern uuid is invalid: {uuid}")

        try:
            ptn = P["pattern"]
        except KeyError:
            raise ValueError(f"Pattern {uuid} does not have a pattern entry")

        try:
            triggers = P["triggers"]
        except KeyError:
            pass

        try:
            map = P["map"]
        except KeyError:
            pass

        if triggers is None and map is None:
            raise ValueError(f"At least one of triggers or map needs to be set: {uuid}")

        try:
            type = P["type"]
        except KeyError:
            raise ValueError(f"Pattern {uuid} does not have a type")

        try:
            name = P["name"]
        except KeyError:
            raise ValueError(f"Pattern {uuid} does not have a name")

        try:
            partition = P["partition"]
        except KeyError:
            raise ValueError(f"Pattern {uuid} does not declare a partition")

        self._uuid = uuid
        self._ptn = ptn
        self._type = type
        self._name = name
        self._triggers = triggers
        self._map = map
        self._partition = partition

    def uuid(self):
        return self._uuid

    def pattern(self):
        return self._ptn

    def type(self):
        return self._type

    def name(self):
        return self._name

    def triggers(self):
        return self._triggers

    def map(self):
        return self._map

    def mappings(self):
        return self._mappings

    def partition(self):
        return self._partition

    def print(self):
        print(
            "\tname: ",
            self._name,
            "\tuuid: ",
            self._uuid,
            "\ttype: ",
            self._type,
            "\tpartition: ",
            self._partition,
            "\tpattern: ",
            self._ptn,
        )

    def to_string(self):
        return "{ \"name\": \"" + self._name + "\", \"uuid\": \"" + self._uuid + "\", \"type\": \"" + self._type + "\", \"partition\": \"" + self._partition + "\"}"
        


class RegexPattern(Pattern):
    def __init__(self, P, UuidStore):
        super().__init__(P, UuidStore)
        self._map = {}
        try:
            self._map = P["map"]
        except KeyError:
            if self.triggers() == None:
                raise ValueError(
                    "A regex pattern must have at least one triggers or map statement"
                )

    def map(self):
        return self._map


# pattern:
#   .some_path: value
#   .other_path:
# This will be translated to
#   {'.some_path':'value','.other_path':None}
class StructuredPattern(Pattern):
    def __init__(self, P, UuidStore):
        super().__init__(P, UuidStore)
        self._match = []

        Ptn = super().pattern()

        for p, v in Ptn.items():
            if v is not None:
                self._match.append(p + ":" + v)
            else:
                self._match.append(p)

    def match(self):
        return self._match


class Rule:
    def __init__(self, uuid, name, patterns, UuidStore):
        if not UuidStore.validate(uuid):
            raise ValueError(f"uuid is invalid: {uuid}")

        self._uuid = uuid
        self._name = name
        self._patterns = patterns

    def uuid(self):
        return self._uuid

    def name(self):
        return self._name

    def patterns(self):
        return self._patterns

    def print(self):
        print("uuid: ", self._uuid)
        print("name: ", self._name)
        print("patterns: ")
        for ptn in self._patterns:
            ptn.print()


def load_yaml(FName):
    try:
        f = open(FName)
        Yaml = yaml.load(f, Loader=yaml.FullLoader)
    except FileExistsError:
        raise ValueError(f"File {FName} does not exist")
    finally:
        f.close()

    return Yaml


def _construct_pattern(Ptn, UuidStore):
    try:
        Type = Ptn["type"]
    except KeyError:
        raise ValueError(f"Pattern has no type: {Ptn}")

    if Type == "regex":
        return RegexPattern(Ptn, UuidStore)
    elif Type == "kv" or Type == "json":
        return StructuredPattern(Ptn, UuidStore)

    raise ValueError(f"Unknown pattern type {Type}")


def _get_rule_patterns(Ptns, UuidStore):
    Patterns = []
    for P in Ptns:
        Ptn = _construct_pattern(P, UuidStore)
        Patterns.append(Ptn)

    return Patterns


def get_rules(FName, UuidStore):
    """
    Get the patters from a YAML file and validate that entries are correct
    Args:
        path to a valid YAML rules file

    Returns:
        A list of filled out Rule object

    Exceptions:
        VaueError: Thrown when a yaml rule file contains a bad entry
    """

    YamlRule = None

    try:
        YamlRules = load_yaml(FName)
    except ValueError as e:
        print(f"Bad YAML {e}")
        raise ValueError(f"invalid YAML file {FName}")

    ParsedRules = []

    for YamlRule in YamlRules:
        Patterns = []
        ID = None
        Name = None
        Ptns = None

        try:
            ID = YamlRule["id"]
        except KeyError:
            raise ValueError(f"Rule in file {FName} has no id")

        try:
            Name = YamlRule["name"]
        except KeyError:
            raise ValueError(f"Rule {ID} in file {FName} has no name")

        try:
            Ptns = YamlRule["patterns"]
        except KeyError:
            raise ValueError(f"Rule {ID} in file {FName} has no patterns")

        Patterns = _get_rule_patterns(Ptns, UuidStore)
        ParsedRules.append(Rule(ID, Name, Patterns, UuidStore))

    return ParsedRules


def build_partitions(Rules):
    Partitions = {}
    for Rule in Rules:
        for Ptn in Rule.patterns():
            Part = Ptn.partition()
            PtnList = []
            try:
                PtnList = Partitions[Part]
            except KeyError:
                Partitions[Part] = PtnList

            if Part == "root" and Ptn.type() != "regex":
                raise ValueError(
                    f"Root partitoin can only contain regex patterns: {Ptn.uuid()}:{Ptn.type()}"
                )

            PtnList.append(Ptn)

    return Partitions


def main(file):
    Rules = get_rules(file)

    # set up patterns by partition
    Partitions = build_partitions(Rules)

    print("==> Partitions:")
    for Name, Part in Partitions.items():
        print("Name: ", Name)
        for P in Part:
            P.print()

    print("==> Rules:")
    for Rule in Rules:
        Rule.print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("please supply a file to parse")
    else:
        main(sys.argv[1])
