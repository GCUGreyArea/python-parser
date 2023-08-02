# parser

## Basic operation 

You can run the parsers against a defined set of `rules` and `messages` with the command `./parse.py rules logs`. To get formated json output run `./parse.py rules logs | jq`. Please note that this requires `jq` to be correctly installed in your system.

## Basic architecture 

The parser breaks down a parsing problem into recognition and extraction phases, allowing one pattern to delegate ectraction of tokens to another. Put simply, a string that contains something like `name=Barry Robinson,status={"company":"Northrup Grumman","job":"Lead Cyber Engineer","opinion":"favourable"}` might be broken into 2 sepperat fragments based on format. 

1. `name=Barry Robinson` which is `kv`
2. `{"company":"Northrup Grumman","job":"Lead Cyber Engineer","opinion":"favourable"}` which is `json`

This would happen by having a `root` pattern recognise the initial `kv` string format, and route it to a `kv` parser. If the `status={...}` is the unique part, a simple `regex` can be created to identify this message and route it to a specific `kv` pattern that will extract the fragments and eith map them to tokens or route them to a new pattern for reparsing. 

The `framework` does this by ingesting rules that are a set of declarations and patterns that it can then execut against a message string. 

The framework can be executed by running `./framework.py <rules dir> <message>` where

    rules dir: A directory containing YAML rule files
    message: A message the the rules can decode

An example rule file is presented beow 

```yaml
- id: bf1d64ad-9694-4317-b7a6-55e9a4915437
  name: test rule
  patterns: 
    - id: f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537
      name: aws json
      type: regex 
      partition: root
      pattern: '^aws: (?P<json>{.*})'
      triggers:
        - name: json
          format: regex
          partition: aws regex
    - id: eb4963b9-3fa5-4338-8a40-01a35fecc782
      name: aws regex
      type: regex
      partition: aws regex
      pattern: '^{"name":"(?P<name>[\w ]+)","satisfaction":"(?P<satisfaction>[\w ]+)"}'
      map:
        name: name
        satisfaction: value
```

With this rule the string `'aws: {"name":"Barry Robinson","value":"high"}'` is first matched by trhe pattern `f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537` whose trigger is setup to forward the text extracted by the `json` capture group to to a `regex` partition called `aws regex`. 

Pattern `eb4963b9-3fa5-4338-8a40-01a35fecc782` recives the text and parses `name` and `value`, which, due to the `map` statement is maped to the tokens `name` and `value`

If no rules with patterns for the message exists, an empty map is returned. 

If a rule (or set of rules and patterns) exists that can parse the message, a map of `{'token name':'token value'}` is returned for the tokanized message. 

The above rule, for the message `'aws: {"name":"Barry Robinson","satisfaction":"high"}'` yields the output `{"rule": "bf1d64ad-9694-4317-b7a6-55e9a4915437", "pattern": ["f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537", "eb4963b9-3fa5-4338-8a40-01a35fecc782"], "tokens": {"name": "Barry Robinson", "value": "high"}}`

With `jq formating` the command `./framework.py resources/framework_two/ 'aws: {"name":"Barry Robinson","satisfaction":"high"}' | jq` will format to

```json
{
  "rule": "bf1d64ad-9694-4317-b7a6-55e9a4915437",
  "pattern": [
    "f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537",
    "eb4963b9-3fa5-4338-8a40-01a35fecc782"
  ],
  "tokens": {
    "name": "Barry Robinson",
    "value": "high"
  }
}
```

For more details about the parser please checkout the [parser design document](docs/design.md).

## Note 

1. Might not be maximally efficient

## Todo 

1. Pre defined tokens with types instead of auto formating
