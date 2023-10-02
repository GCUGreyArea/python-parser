#!/usr/bin/env python3

import sys
import os
import re
from rules import get_rules, build_partitions, GlobalUuid
from kv_py_parse import KVParser
from fragments import decode_fragment
import json
from json_py_parse import parse_json

# An action can either map to a token name
# or require that the fragment to with the
# action belongs to be reparsed.
#
# In the case of a token the action will contain
# the name of token the fragment should be expressed
# as.
#
# In the case of forwarding the action will contain
# the name and type of the partition that the
# fragment should be forwarded to as a string in the
# form name:type.
#
# A flag will tell the Framework which type of action
# this is.


class Action:
    def __init__(self, string, flag):
        self._string = string
        self._map = flag

    def is_map(self):
        return self._map

    def string(self):
        return self._string

    def to_string(self):
        m = None
        if self._map:
            m = "map"
        else:
            m = "forward"

        return self._string + " => " + m


# Each engine contains all the patterns for that type in the partition there can
# be multiple engine types in the same partition but all patterns for that type
# in that partition will reside with that one engine. That is to say that all
# regex patterns for partition 'some value' will be assigned to a single regex
# engine. Consiquently all KV patterns in the pattition will be assigned to a KV
# engine.
class Engine:
    def __init__(self, type):
        self._type = type
        self._pattern_by_uuid = {}

    def add_pattern(self, ptn):
        if ptn.type() != self._type:
            raise ValueError(f"Pattern has the wrong type: {ptn.type()}")

        self._pattern_by_uuid[ptn.uuid()] = ptn

    def assemble_action_map(self, triggers, maps):
        action_map = {}
        if triggers is not None:
            for t in triggers:
                name = t["name"]
                format = t["format"]
                partition = t["partition"]
                action_map[name] = Action(partition + ":" + format, False)
        if maps is not None:
            for path, label in maps.items():
                action_map[path] = Action(label, True)

        return action_map

    def print(self):
        print("type: ", self._type)
        for p in self._pattern_by_uuid:
            p.print()

    def to_string(self):
        st = "{\"type\": \"" + self._type + "\", \"values\": ["
        for _, p in self._pattern_by_uuid.items():
            if st[-1] != "[":
                st += ","
            st += p.to_string()

        return st + "]}"


# Engine for regex parsing
class RegexEngine(Engine):
    def __init__(self):
        super().__init__("regex")
        self._reg = []

    def print(self):
        super().print()

    def finalise(self):
        for _, p in self._pattern_by_uuid.items():
            triggers = p.triggers()
            maps = p.map()
            action_map = self.assemble_action_map(triggers, maps)
            # Add this is a tuple
            self._reg.append((re.compile(p.pattern()), action_map, p))

    def parse(self, frag_str):
        for ptn, act_map, p in self._reg:
            FrgList = []
            m = ptn.match(frag_str)
            if m:
                # In regex all named groups must have some kind of action or map
                # statement
                for name, index in ptn.groupindex.items():
                    val = m.group(index)
                    action = act_map[name]
                    FrgList.append((val, action))

                return (p, FrgList)

        # default to the empty list
        return None


# engine for kv parsing
class KvEngine(Engine):
    def __init__(self, KSep="=", VSep=","):
        super().__init__("kv")
        self._ksep = KSep
        self._vsep = VSep
        self._matches = []

    def parse(self, string):
        parser = KVParser(string, self._ksep, self._vsep)
        parser.run_parser()
        FrgList = []
        Ret = (None, FrgList)
        found = 0
        # _matches now needs to contain the path and the action to take
        for matches, action_map, ptn in self._matches:
            Ret = (ptn, FrgList)

            for key in matches:
                if parser.contains(key) is None:
                    break
                found += 1

            if found == len(matches):
                Ret = (ptn, FrgList)
                # map tokens, if a path doesn't exist, continue
                for path, act in action_map.items():
                    v = parser.contains(path)
                    if v is not None:
                        FrgList.append((v, act))
                return Ret
            # go to next match pattern
            found = 0

        return None

    def print(self):
        super().print()

    def finalise(self):
        for _, p in self._pattern_by_uuid.items():
            triggers = p.triggers()
            maps = p.map()
            action_map = self.assemble_action_map(triggers, maps)
            self._matches.append((p.match(), action_map, p))


# engine for json parsing
class JsonEngine(Engine):
    def __init__(self):
        super().__init__("json")
        self._matches = []

    def print(self):
        super().print()

    def finalise(self):
        for _, p in self._pattern_by_uuid.items():
            triggers = p.triggers()
            maps = p.map()
            action_map = self.assemble_action_map(triggers, maps)
            self._matches.append((p.match(), action_map, p))

    def parse(self, string):
        HDict = parse_json(string)
        FrgList = []
        Ret = (None, FrgList)
        found = 0
        # _matches now needs to contain the path and the action to take
        for matches, action_map, ptn in self._matches:
            Ret = (ptn, FrgList)

            for key in matches:
                try:
                    HDict[key]
                    found += 1
                except KeyError:
                    found = 0
                    break

            if found == len(matches):
                # Map tokens. If we fail to find a path, just carry on
                Ret = (ptn, FrgList)
                for path, act in action_map.items():
                    try:
                        v = HDict[path]
                        FrgList.append((v, act))
                    except KeyError:
                        continue
                return Ret
            # go to the next match pattern
            found = 0

        # return whatever we matched
        return None


# Framework class to run parsers
class Framework:
    def __init__(self, rule_dir):
        self._uuid_store = GlobalUuid()
        # Find all flies that end in "yaml" and who's names are a mix of letters and numbers
        Files = [
            os.path.join(dp, f)
            for dp, dn, fn in os.walk(os.path.expanduser(rule_dir))
            for f in fn
            if re.match(r"[\w\d]+\.yaml", f)
        ]
        self._partitions = {}
        self._rule_by_id = {}
        self._rule_by_pattern_id = {}
        self._engines = {}

        for File in Files:
            RuleList = get_rules(File, self._uuid_store)
            for Rule in RuleList:
                self._rule_by_id[Rule.uuid()] = Rule

            self._build_rule_by_pattern_id(RuleList)
            part = build_partitions(RuleList)
            for p,l in part.items():
                try: 
                    pl = self._partitions[p]
                    pl.extend(l)
                except KeyError:
                    self._partitions[p] = l

        self._engines.update(self._build_parsing_engines())

    def _build_parsing_engines(self):
        engines = {}
        for PartName, PartList in self._partitions.items():
            for Ptn in PartList:
                eng = None
                type = Ptn.type()
                name = PartName + ":" + type

                try: 
                    eng = engines[name]
                except KeyError: 
                    if type == "regex":
                        eng = RegexEngine()
                    elif type == "kv":
                        eng = KvEngine()
                    elif type == "json":
                        eng = JsonEngine()
                    else:
                        raise ValueError(f"Unnkonw engine type : {type}")
                finally:
                    engines[name] = eng

                eng.add_pattern(Ptn)

        for _, e in engines.items():
            e.finalise()

        return engines

    def _build_rule_by_pattern_id(self, RuleList):
        RuleMap = {}
        for Rule in RuleList:
            PtnList = Rule.patterns()
            for Ptn in PtnList:
                RuleMap[Ptn.uuid()] = Rule

        self._rule_by_pattern_id.update(RuleMap)

    # @profile
    def parse_fragment(self, FragStr, partition):
        try:
            eng = self._engines[partition]
        except KeyError:
            raise ValueError(f"no patterns found in {partition} in parse_fragment")

        Ret = eng.parse(FragStr)

        if Ret is None:
            return None

        (Ptn, FragList) = Ret
        tokens = {}
        ptnList = []
        ptnList.append(Ptn.uuid())
        for frag, action in FragList:
            if action.is_map():
                v = decode_fragment(frag)
                tokens[action.string()] = v
            else:
                Ret = self.parse_fragment(frag, action.string())
                if Ret is None:
                    return None

                (PtnList, res) = Ret
                for p in PtnList:
                    ptnList.append(p)
                tokens.update(res)

        return (ptnList, tokens)

    def print(self):
        print("engines:")
        for _, eng in self._engines.items():
            eng.print()

    def to_string(self):
        st = "["
        for _, eng in self._engines.items():
            if st != "[":
                st = st + ","
            st = st + eng.to_string()
        

        return st + "]"

    def generate_output_map(self, UuidList, parse_map):
        RuleMap = {}
        RuleList = []
        for uuid in UuidList:
            R = self._rule_by_pattern_id[uuid]
            Ruuid = R.uuid()
            try:
                RuleMap[Ruuid]
            except KeyError:
                RuleMap[Ruuid] = Ruuid
                RuleList.append(Ruuid)

        out = {}
        if len(RuleList) == 0:
            pass
        elif len(RuleList) == 1:
            out["rule"] = RuleList[0]
        else:
            out["rule"] = RuleList

        if len(UuidList) == 0:
            pass
        elif len(UuidList) == 1:
            out["pattern"] = UuidList[0]
        else:
            out["pattern"] = UuidList

        out["tokens"] = parse_map

        return out

    def generate_json_output(self, UuidList, parse_map):
        out = self.generate_output_map(UuidList, parse_map)
        return json.dumps(out)


def main(dir, message):
    f = Framework(dir)
    ret = f.parse_fragment(message, "root:regex")
    if ret is not None:
        (PtnList, Token) = ret
        out = f.generate_json_output(PtnList, Token)
        print(out)
    # print(f.to_string())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: ./framework.py <rule dir> <message>")
        print("rule dir: The root directory for rules files")
        print("message: The message to parse using the rules")
    else:
        main(sys.argv[1], sys.argv[2])
