# Python memsage parser: Design document 

## Project scope 

This is a development excersise to learn python, and should not be considered a finsished, production ready system. As such the goal is to deploy a system in python that is supperficially of use. 

## Goals of design 

1. Create a relatively chalanging system in python
2. expose to 
    1. file handling 
    2. multi file / module system 
    3. unit tests
    4. library use
    5. classes and function
    6. input output formating
3. program structure
4. idiomatic python development

## Design 

The design is loosely 

```
[Msg] submited to -> [Framework] extracts and submits fragments -> [Engines] extracts tokens and triggers -> [Result] output as JSON
```

1. The framework tests messages against all patterns in the `root` partition. 
2. If a pattern matches, the `framework` checs for the pressence or triggers, or a `map` section.
    1. if a `triggers` sectin exists, the matched message fragmens are routed to new engines acording to the specified `triggers` directives.
    2. if a `map` section is found the `capture groups` (in the case of regex), are mapped to tokens of the specified name under the `tokens` entry of the `json` output.  
3. when no more `triggers` are encountered, parsing completes and the `tokens` that have been mapped are returned, along with details of the matching rule, and patterns.  


## Classes and structures 

- a map of lists of patterns by partition
    - pattern must contain
        - it's UUID
        - the pattern itself
        - the name of the pattern
        - list of triggers 
        - list of mappings
        - partition
## Todo 

1. design and build simple representation for parsing engines to work on
    1. must be able to deal with partitions
2. design and build a framework to access parsing engines and route messages to the correct partition