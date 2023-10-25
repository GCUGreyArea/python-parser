# Results analytics

## Notes

1. To use JQ Paths we are going to need to to replicate the functionality use by
   the JSON parser when it renders JSON to paths / values.  

## The analyser 

The analyser provides simple data normalisation and conversion through YAML
rules located in the `rules` directory. 

## Data normalisation and conversion rules 

These can be found in the `rules` directory under `analyser`. The rules specify
transformatin that can be used to normalise data for things like date and time
formats. 

## Even rules

Thes can be found under `meta_data` in `analyser`. They are used specify the
conditions tha determin raising an event. An event is a system wide state that
is set into a database and can be convied to an end user based on corrolation of
data elements. 

### Language definitoin 

The following is a language description in [Bachus Naur
form](https://en.wikipedia.org/wiki/Backus-Naur_form) for the langauge component
of the event system. This is the part that defines rules for events that are
triggered by new messages.

```
<msg_path>              ::= (:?rule|pattern|client_id)\b
<field_path>            ::= tokens\.[a-zA-Z][a-z\_\.]*\b
<collection>            ::= (:?messages|updates|status)\b
<table_ref>             ::= table\.[a-z][a-z\_]*\b
<if>                    ::= 'if'
<then>                  ::= 'then'
<else>                  ::= 'else'
<contains>              ::= 'contains'
<count>                 ::= 'count'
<sum>                   ::= 'sum'
<in>                    ::= 'in'
<where>                 ::= 'where'
<assert>                ::= 'assert'
<using>                 ::= 'using'
<int>                   ::= \d+
<float>                 ::= \d+.\d+
<string>                ::= '\"[^\"]\"
<literal_value>         ::= <int> | <float> | <string>
<equal>                 ::= '='
<plus_equal>            ::= '+='
<minus_equal>           ::= '-='
<div_equal>             ::= '/='
<less_than>             ::= '<'
<greater_than>          ::= '>'
<greater_or_equal>      ::= '>='
<less_or_equal>         ::= '<='
<comparison>            ::= <equals> | <greater_than> | <less_than> | <greater_or_equal> | <less_or_equal>
<sys_var>               ::= $NOW | $TODAY
<db_constraint>         ::= <db_path> <comparison> <literal_value>
<db_constraint_list>    ::= <db_constraint> <and> <db_constraint> | <db_contraint> <or> <db_constraint>
<db_count_expr>         ::= <count> <db_path> <where> <db_constraint_list>
<db_sum_expr>           ::= <sum> <db_path> <where> <db_constraint_list>
<db_expr>               ::= <db_count_expr> | <db_sum_expr> | 
<lookup_expr>           ::= <msg_path> <in> <table_ref>
<field_db_expr>         ::= <field_path> <comparison> <db_path> <db_constraint_list>
<db_assign_expr>        ::= <db_path> <assign> <msg_path> | <db_path>
```

```
using messages clients collect "client_id";
for all clients get client
   using messages query1 {"client_id" : client, "ruler":"b489a151-6e84-43ce-86d2-40e21791b26b"} aggregate;
   using status query2 {"client_id" : client};
   if query1.tokens.notification.ilegal loggin attempt" >= 3 and
      query1.tokens.file contains "/opt/dev/device"
         then assert status.breach_attempt += 1;
   if query1.tokens.machine is "DESKTOP-TJR7EI0" and
      query2.breach_attempt > 3
         assert status.allert = true
```

The above example of an event rule that does very litle in the real world, but
it should be remeberd that this is a toy system.


## TODO 

1. Make the rule compiler look ahead to conserve effort and only agregate or
   render values that will be used instead of the complete map of returned
   values. For instance in the above exampole query the first part of the query
   collects all the client_id from the message database which gives all the
   clients that have been effected byt some incident. For every client, the the
   next two queries are run 

```
using messages query1 {"client_id" : client, "ruler":"b489a151-6e84-43ce-86d2-40e21791b26b"} aggregate;
using status query2 {"client_id" : client};
```

The first part of this would aggregate all the values when the rest of the query
only uses query1.tokens.notification.ilegal loggin attempt" and
query1.tokens.machine, which are the only values that we need to collect
(because no other value is accessed). The ideal way to achive this is to
restrict the returned values from the query to the fields used by other parts of
the query, but also only aggregate .tokens.notification.ilegal loggin attempt".

