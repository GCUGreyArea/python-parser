# parser

## Basic operation 

NOTE: All python files are now under `app` so that the application can be neetly
containerised.

You can run the parsers against a defined set of `rules` and `messages` with the
command `./parse.py rules logs`. To get formated json output run `./parse.py
rules logs | jq`. Please note that this requires `jq` to be correctly installed
in your system.

This will currently generate the output 
```json
{
  "result-0": {
    "rule": "bf1d64ad-9694-4317-b7a6-55e9a4915437",
    "pattern": [
      "46975537-6a3c-444a-9784-ea3c1d7e25d3",
      "451a6827-da96-466a-aa97-d73b5605a13f"
    ],
    "tokens": {
      "name": "Barry Robinson",
      "job": "Lead Cyber Engineer",
      "chalange": "ok"
    }
  },
  "result-1": {
    "rule": "bf1d64ad-9694-4317-b7a6-55e9a4915437",
    "pattern": [
      "0b1db7a5-0308-4bfb-87e3-b2a48cee6b88",
      "f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537",
      "ed395291-65d2-492c-afb8-d1b64599263c"
    ],
    "tokens": {
      "latitude": 52.4862,
      "longetude": 1.8904,
      "name": "Barry Robinson",
      "ocupation": "Lead Cyber Engineer",
      "expectation": "chalanging",
      "tag": "v1.0"
    }
  }
}
```


## Unit tests 

Unit tests can be run with the command `./test_parsers.py`


## REST API

The file `server.py` creates a very basic REST API that can be accessed on
`127.0.0.1:5000/parser` using `POST`. With trhe server running, the command
`curl -X POST -d 'message=name=Barry Robinson,job=Lead Cyber
Engineer,expectation=Chalanging work,freeform=latitude 52.4862 longetude 1.8904'
http://127.0.0.1:5000/parse | jq` will produce the output 

```json
{
  "rule": "bf1d64ad-9694-4317-b7a6-55e9a4915437",
  "pattern": [
    "0b1db7a5-0308-4bfb-87e3-b2a48cee6b88",
    "f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537",
    "ed395291-65d2-492c-afb8-d1b64599263c"
  ],
  "tokens": {
    "latitude": 52.4862,
    "longetude": 1.8904,
    "name": "Barry Robinson",
    "ocupation": "Lead Cyber Engineer",
    "expectation": "Chalanging work"
  }
}
```

## Running the docker 

The docker files `server.dockerfile` and `docker-compose.yml` are supplied for
containerisation of the flask server. To buid and run the server

```shell
$ docker-compose build 
$ docker-compose up 
```

You should see 

```shell
$ docker-compose up
Recreating server ... done
Attaching to server
server    |  * Serving Flask app 'server'
server    |  * Debug mode: off
server    | WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
server    |  * Running on all addresses (0.0.0.0)
server    |  * Running on http://127.0.0.1:5000
server    |  * Running on http://172.20.0.2:5000
server    | Press CTRL+C to quit
```

You should now be able to access the server with `curl -X POST -d
'message=name=Barry Robinson,job=Lead Cyber Engineer,expectation=Chalanging
work,freeform=latitude 52.4862 longetude 1.8904'  http://127.0.0.1:5000/parse |
jq`. If you wish to add new rules to the containerised server you will need to
update or add to the existing `YAML` rules in `rules` (which is where the server 
defaults to), then rebuild the container with `docker-compose build`.

## Basic architecture 

### Simple explanation

The parser breaks down a parsing problem into recognition and extraction phases,
allowing one pattern to delegate ectraction of tokens to another. Put simply, a
string that contains something like `name=Barry
Robinson,status={"company":"Northrup Grumman","job":"Lead Cyber
Engineer","opinion":"favourable"}` might be broken into 2 sepperat fragments
based on format. 

1. `name=Barry Robinson` which is `kv`
2. `{"company":"Northrup Grumman","job":"Lead Cyber
   Engineer","opinion":"favourable"}` which is `json`

This would happen by having a `root` pattern recognise the initial `kv` string
format, and route it to a `kv` parser. If the `status={...}` is the unique part,
a simple `regex` can be created to identify this message and route it to a
specific `kv` pattern that will extract the fragments and eith map them to
tokens or route them to a new pattern for reparsing. 

The `framework` does this by ingesting rules that are a set of declarations and
patterns that it can then execut against a message string. 

The framework can be executed by running `./framework.py <rules dir> <message>`
where

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

With this rule the string `'aws: {"name":"Barry Robinson","value":"high"}'` is
first matched by trhe pattern `f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537` whose
trigger is setup to forward the text extracted by the `json` capture group to 
a `regex` partition called `aws regex`. 

Pattern `eb4963b9-3fa5-4338-8a40-01a35fecc782` recives the text and parses
`name` and `value`, which, due to the `map` statement, are maped to the tokens
`name` and `value`

The above rule, for the message `'aws: {"name":"Barry
Robinson","satisfaction":"high"}'` yields the output `{"rule":
"bf1d64ad-9694-4317-b7a6-55e9a4915437", "pattern":
["f28a4fcc-32dd-4c4b-afd6-4aca3e4f5537",
"eb4963b9-3fa5-4338-8a40-01a35fecc782"], "tokens": {"name": "Barry Robinson",
"value": "high"}}`

With `jq formating` the command `./framework.py resources/framework_two/ 'aws:
{"name":"Barry Robinson","satisfaction":"high"}' | jq` will format to

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

### Rules about rules 

1. Where a `path` is expressed in a `structured pattern` (JSON or KV) as part of
  `pattern` the rule is telling the parser to ONLY match if those paths are
  present with the values supplied 
    1. A value of `.name:` means `match if the
       parth is pressent` 
    2. A value of `.name: Value` means match only if the
       path exists and has the supplied value.
2. Where a map directive is supplied, i.e. `.path: label` the value at `.path`
   will be mapped to the `label` supplied IF IT EXISTS IN THE MESSAGE. Otherwise
   it will be ignored. Its absence will not prevent the message from matching a rule
   if a suitable rules exists.
3. If any sub pattern fails, the entire chain of patterns fails. 
    1. The parser will try to find another match.
    2. If no new match can be found, the parsing actin fails 

For more details about the parser please checkout the [parser design document](docs/design.md).

### Rules about partitions and patterns 

The general idea is that a `partition` should not constain a large number of
`patterns`. The basic architecture for recognising a `message` means that a top
level `root` pattern should do the main work of recognising the `message` type,
then forward the reevant `fragments` to partitions with some patterns in it to do
extraction of values. The more patterns in a paratition, the less efficient the
parser becomes, because the more patterns it needs to try. It's that simple.

In genreal a rule should be considered a top level grouping of similar patterns
that deals with a single message type. In the world of log messages that might
be like `AWS ReddShift` logs messages. 

## Note and other considerations 

1. Might not be maximally efficient
2. The ability to express an `SIEM` `event` by using conditional logic. This
   would need to refer to token valules to create new values. See [Token based
   extensible message parser -
   CheckPoint.yaml](https://github.com/GCUGreyArea/regex-parser/blob/f5347f39beee12cab84b9da09c056262c1c95899/rules/Checkpoint/CheckPoint.yaml#L39)

## Todo 

1. Pre defined tokens with types instead of auto formating
2. Implement `contains` logic `json` patterns i.e. `.development.languages[]
   contains c++` for the `json`
   `{"development":{"languages":["java","c","python","c++"]}}`
3. The server should be able to handle bach requests for parsing to be usefull.
4. There better diagnostic tools through exceptions.
5. There should be proper loging.
6. The parser could be made significantly more efficient by using `Hyperscan` for
   Python to do regex matching and `RE2` for extraction.
7. Structured patterns are grossly inificient. 


## Glossary of terms 

- **Message**: Some structured or unstructured text needing tokanisation
- **Structured pattern**: A pattern for a structured format such as JSON or KV
  expressed using JQ Paths. 
- **Partition**: A named segmentation of parsing search space. Within the
  current architecture `partitions` are attached to specific formats such that a
  partition resolves to `name:format`, i.e. `basic kv:kv`. 
- **Rules flie**: A rule, written in `YAML`, that groups together `patterns`,
  along with their respective `map` and `trigger` directives to program the `the
  framework` of the parser.
- **Framework**: The code responsible for marsheling `parsing engines` to
  acomplish the classification and extraction of `token` values from some
  string.
- **Token**: A named tage for a value expressed in a pattern's `map` criteria.
- **Trigger**: A directive that programs the parser to resubmit a fragment for
  further parsing by the specified `engine`, using the specified `partition`.
- **Engine**: A grouping of `patterns` attached to a specific `format` and
  `partition`, along with the functionality to extract `fragments` from that
  format and direct the parser to perform the correct `actions`, i.e. to `map`
  to `tokens` or `trigger` further parsing.

## Usefull linnks 

  - [SIEM](https://www.sumologic.com/glossary/siem-log)
  - [Hyperscan python](https://python-hyperscan.readthedocs.io/en/latest/)
  - [Hyperscan](https://www.intel.com/content/www/us/en/developer/articles/technical/introduction-to-hyperscan.html)
  - [Hyperscan git repo](https://github.com/intel/hyperscan)
  - [Python RE2](https://pypi.org/project/re2/)
