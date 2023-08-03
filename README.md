# parser

## Basic operation 

You can run the parsers against a defined set of `rules` and `messages` with the
command `./parse.py rules logs`. To get formated json output run `./parse.py
rules logs | jq`. Please note that this requires `jq` to be correctly installed
in your system.

## Unit tests 

Unit tests can be run with the command `./test_parsers.py`


## REST API

The file `server.py` creates a very basic REST API that can be accessed on `127.0.0.1:5000/parser` using `POST`. With trhe server running, the command `curl -X POST -d 'message=name=Barry Robinson,job=Lead Cyber Engineer,expectation=Chalanging work,freeform=latitude 52.4862 longetude 1.8904'  http://127.0.0.1:5000/parse | jq` will produce the output 

```shell
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   453  100   331  100   122  36777  13555 --:--:-- --:--:-- --:--:-- 50333
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

The docker files `server.dockerfile` and `docker-compose.yml` are supplied for containerisation of the flask server. To buid and run the server

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
defaults to, then rebuild the container with `docker-compose build`.

## Basic architecture 

## Simple explanation

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
   it will be ignored, but it will not prevednt the messate from matching a rule
   if one exists.

For more details about the parser please checkout the [parser design document](docs/design.md).

## Note 

1. Might not be maximally efficient

## Todo 

1. Pre defined tokens with types instead of auto formating
2. Implement `contains` logic `json` patterns i.e. `.development.languages[]
   contains c++` for the `json`
   `{"development":{"languages":["java","c","python","c++"]}}`
