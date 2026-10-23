#!/usr/bin/env python3
"""Génère les 4 plans de test JMeter (.jmx) de l'étude de cas.

Les valeurs nominales du TP sont utilisées par défaut (ramp-up 60 s,
durée 10 min par palier). Elles sont surchargeables à l'exécution :

    jmeter -n -t jmeter/read-heavy.jmx -Jhost=localhost -Jport=8082 \\
           -Jramp=60 -Jhold=600 -l report/results/read-heavy-C.jtl

Propriétés reconnues :
    host         hôte cible                        (défaut localhost)
    port         port cible                        (défaut 8082)
    base         URL de base (variante D / liens)  (défaut http://localhost:8082)
    pageSize     taille de page                    (défaut 50)
    bycatPath    chemin du filtre par catégorie    (défaut /items?categoryId=)
                 variante D : /items/search/byCategory?categoryId=
    itemBody     payload léger de POST /items      (défaut item-light-ac.json)
    heavyBody    payload lourd de POST /items      (défaut item-heavy-ac.json)
    dataDir      répertoire des CSV/payloads       (défaut jmeter/data)
    ramp         ramp-up en secondes               (défaut 60)
    hold         durée d'un palier en secondes     (défaut 600)
"""
import os
import re
import xml.sax.saxutils as sx

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jmeter")

HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'


def esc(v):
    return sx.escape(str(v), {'"': "&quot;"})


def http_defaults():
    return """
        <ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" testname="HTTP Request Defaults" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${host}</stringProp>
          <stringProp name="HTTPSampler.port">${port}</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
          <stringProp name="HTTPSampler.implementation">HttpClient4</stringProp>
          <stringProp name="HTTPSampler.connect_timeout">10000</stringProp>
          <stringProp name="HTTPSampler.response_timeout">60000</stringProp>
        </ConfigTestElement>
        <hashTree/>
        <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
          <collectionProp name="HeaderManager.headers">
            <elementProp name="" elementType="Header">
              <stringProp name="Header.name">Content-Type</stringProp>
              <stringProp name="Header.value">application/json</stringProp>
            </elementProp>
            <elementProp name="" elementType="Header">
              <stringProp name="Header.name">Accept</stringProp>
              <stringProp name="Header.value">application/json</stringProp>
            </elementProp>
          </collectionProp>
        </HeaderManager>
        <hashTree/>"""


def csv_dataset(name="ids.csv"):
    return """
          <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" testname="CSV Data Set Config (ids)" enabled="true">
            <stringProp name="filename">${__P(dataDir,jmeter/data)}/%s</stringProp>
            <stringProp name="fileEncoding">UTF-8</stringProp>
            <stringProp name="variableNames">cat_id,item_id</stringProp>
            <boolProp name="ignoreFirstLine">true</boolProp>
            <stringProp name="delimiter">,</stringProp>
            <boolProp name="quotedData">false</boolProp>
            <boolProp name="recycle">true</boolProp>
            <boolProp name="stopThread">false</boolProp>
            <stringProp name="shareMode">shareMode.all</stringProp>
          </CSVDataSet>
          <hashTree/>""" % name


BODY_SCRIPT = """
def base = props.get('dataDir') ?: 'jmeter/data'
def file = vars.get('%s') ?: '%s'
def s = new java.io.File(base + '/' + file).getText('UTF-8')
def shortUuid = java.util.UUID.randomUUID().toString().replace('-', '').substring(0, 16)
s = s.replace('__SHORTUUID__', shortUuid)
s = s.replace('__UUID__', java.util.UUID.randomUUID().toString())
s = s.replace('__CAT__', vars.get('cat_id') ?: '1')
s = s.replace('__BASE__', vars.get('baseUrl') ?: 'http://localhost:8082')
vars.put('requestBody', s)
"""


def sampler(name, path, method="GET", body_slot=None):
    args = """
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" enabled="true">
              <collectionProp name="Arguments.arguments">
                <elementProp name="" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.value">${requestBody}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                </elementProp>
              </collectionProp>
            </elementProp>
            <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>"""
    subtree = "<hashTree/>"
    if body_slot:
        var = body_slot if body_slot in ("itemBody", "heavyBody") else ""
        script = BODY_SCRIPT % (var, body_slot)
        subtree = """<hashTree>
            <JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="Corps de requête (%s)" enabled="true">
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="filename"></stringProp>
              <stringProp name="parameters"></stringProp>
              <stringProp name="script">%s</stringProp>
              <stringProp name="scriptLanguage">groovy</stringProp>
            </JSR223PreProcessor>
            <hashTree/>
          </hashTree>""" % (esc(body_slot), esc(script))
    else:
        args = """
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" enabled="true">
              <collectionProp name="Arguments.arguments"/>
            </elementProp>"""
    return """
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="%s" enabled="true">%s
            <stringProp name="HTTPSampler.path">%s</stringProp>
            <stringProp name="HTTPSampler.method">%s</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
            <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          </HTTPSamplerProxy>
          %s""" % (esc(name), args, esc(path), method, subtree)


def json_extract(ref, expr):
    return """
          <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="Extraire %s (%s)" enabled="true">
            <stringProp name="JSONPostProcessor.referenceNames">%s</stringProp>
            <stringProp name="JSONPostProcessor.jsonPathExprs">%s</stringProp>
            <stringProp name="JSONPostProcessor.match_numbers">1</stringProp>
            <stringProp name="JSONPostProcessor.defaultValues">0</stringProp>
          </JSONPostProcessor>
          <hashTree/>""" % (ref, esc(expr), ref, esc(expr))


def branch_preprocessor(script):
    return """
          <JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="Tirage pondéré de la branche" enabled="true">
            <stringProp name="cacheKey">true</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">%s</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PreProcessor>
          <hashTree/>""" % esc(script)


def group(name, *children):
    """SimpleController : regroupe plusieurs samplers en une seule branche du SwitchController."""
    return """
          <SimpleController guiclass="org.apache.jmeter.control.gui.SimpleControllerGui" testclass="org.apache.jmeter.control.SimpleController" testname="%s" enabled="true"/>
          <hashTree>%s</hashTree>""" % (esc(name), "".join(children))


def switch(*children, value="${branch}"):
    return """
          <SwitchController guiclass="SwitchControllerGui" testclass="SwitchController" testname="Branche %s" enabled="true">
            <stringProp name="SwitchController.value">%s</stringProp>
          </SwitchController>
          <hashTree>%s</hashTree>""" % (esc(value), esc(value), "".join(children))


THREAD_UDV = """
          <Arguments guiclass="ArgumentsPanel" testclass="Arguments" testname="Valeurs par défaut (thread)" enabled="true">
            <collectionProp name="Arguments.arguments">
              <elementProp name="branch" elementType="Argument">
                <stringProp name="Argument.name">branch</stringProp>
                <stringProp name="Argument.value">0</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
              <elementProp name="newItemId" elementType="Argument">
                <stringProp name="Argument.name">newItemId</stringProp>
                <stringProp name="Argument.value">1</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
              <elementProp name="newCatId" elementType="Argument">
                <stringProp name="Argument.name">newCatId</stringProp>
                <stringProp name="Argument.value">1</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
              <elementProp name="newHeavyId" elementType="Argument">
                <stringProp name="Argument.name">newHeavyId</stringProp>
                <stringProp name="Argument.value">1</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
            </collectionProp>
          </Arguments>
          <hashTree/>"""


def thread_group(name, threads, children, serial=False):
    template = """
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="__NAME__" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">-1</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">__THREADS__</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${__P(ramp,60)}</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">${__P(hold,600)}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>__UDV____CHILDREN__
      </hashTree>"""
    return (template.replace("__NAME__", esc(name))
                    .replace("__THREADS__", str(threads))
                    .replace("__UDV__", THREAD_UDV)
                    .replace("__CHILDREN__", children))


def plan(name, description, groups, extra_tree=""):
    udv = """
        <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="Variables" enabled="true">
          <collectionProp name="Arguments.arguments">
            <elementProp name="host" elementType="Argument">
              <stringProp name="Argument.name">host</stringProp>
              <stringProp name="Argument.value">${__P(host,localhost)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
            <elementProp name="port" elementType="Argument">
              <stringProp name="Argument.name">port</stringProp>
              <stringProp name="Argument.value">${__P(port,8082)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
            <elementProp name="baseUrl" elementType="Argument">
              <stringProp name="Argument.name">baseUrl</stringProp>
              <stringProp name="Argument.value">${__P(base,http://localhost:8082)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
            <elementProp name="pageSize" elementType="Argument">
              <stringProp name="Argument.name">pageSize</stringProp>
              <stringProp name="Argument.value">${__P(pageSize,50)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
            <elementProp name="bycatPath" elementType="Argument">
              <stringProp name="Argument.name">bycatPath</stringProp>
              <stringProp name="Argument.value">${__P(bycatPath,/items?categoryId=)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
            <elementProp name="itemBody" elementType="Argument">
              <stringProp name="Argument.name">itemBody</stringProp>
              <stringProp name="Argument.value">${__P(itemBody,item-light-ac.json)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
            <elementProp name="heavyBody" elementType="Argument">
              <stringProp name="Argument.name">heavyBody</stringProp>
              <stringProp name="Argument.value">${__P(heavyBody,item-heavy-ac.json)}</stringProp>
              <stringProp name="Argument.metadata">=</stringProp>
            </elementProp>
          </collectionProp>
        </elementProp>"""
    return HEADER + """<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="%s" enabled="true">
      <stringProp name="TestPlan.comments">%s</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">true</boolProp>%s
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>%s
%s
    </hashTree>
  </hashTree>
</jmeterTestPlan>
""" % (esc(name), esc(description), udv, http_defaults(), groups)


# ---------------------------------------------------------------- READ-heavy
read_script = """
def r = new java.util.Random().nextInt(100)
vars.put('branch', r < 50 ? '0' : (r < 70 ? '1' : (r < 90 ? '2' : '3')))
"""
read_children = csv_dataset() + branch_preprocessor(read_script) + switch(
    sampler("GET /items (page,size)", "/items?page=0&size=${pageSize}"),
    sampler("GET /items?categoryId", "${bycatPath}${cat_id}&page=0&size=${pageSize}"),
    sampler("GET /categories/{id}/items", "/categories/${cat_id}/items?page=0&size=${pageSize}"),
    sampler("GET /categories (page,size)", "/categories?page=0&size=${pageSize}"))

read_heavy = plan(
    "READ-heavy (relation incluse)",
    "50% GET /items?page=&size=50 - 20% GET /items?categoryId= - 20% GET /categories/{id}/items - 10% GET /categories",
    thread_group("READ-heavy 50 threads", 50, read_children)
    + thread_group("READ-heavy 100 threads", 100, read_children)
    + thread_group("READ-heavy 200 threads", 200, read_children))

# ---------------------------------------------------------------- JOIN-filter
join_script = """
def r = new java.util.Random().nextInt(100)
vars.put('branch', r < 70 ? '0' : '1')
"""
join_children = csv_dataset() + branch_preprocessor(join_script) + switch(
    sampler("GET /items?categoryId (JOIN)", "${bycatPath}${cat_id}&page=0&size=${pageSize}"),
    sampler("GET /items/{id} (JOIN)", "/items/${item_id}"))

join_filter = plan(
    "JOIN-filter ciblé",
    "70% GET /items?categoryId= - 30% GET /items/{id}",
    thread_group("JOIN-filter 60 threads", 60, join_children)
    + thread_group("JOIN-filter 120 threads", 120, join_children))

# ---------------------------------------------------------------- MIXED
mixed_script = """
def r = new java.util.Random().nextInt(100)
if (r < 40) { vars.put('branch', '0') }
else if (r < 60) { vars.put('branch', '1') }
else if (r < 80) { vars.put('branch', '2') }
else if (r < 90) { vars.put('branch', '3') }
else { vars.put('branch', '4') }
"""
mixed_children = csv_dataset() + branch_preprocessor(mixed_script) + switch(
    sampler("GET /items (page,size)", "/items?page=0&size=${pageSize}"),
    sampler("POST /items (1 KB)", "/items", "POST", "itemBody"),
    sampler("GET /items/{id}", "/items/${item_id}"),
    sampler("POST /categories", "/categories", "POST", "category-light.json"),
    sampler("PUT /categories/{id}", "/categories/${cat_id}", "PUT", "category-light.json"))

mixed = plan(
    "MIXED (écritures sur deux entités)",
    "40% GET /items - 20% POST /items (1 KB) - 20% GET /items/{id} - 10% POST /categories - 10% PUT /categories/{id}",
    thread_group("MIXED 50 threads", 50, mixed_children)
    + thread_group("MIXED 100 threads", 100, mixed_children))

# ---------------------------------------------------------------- HEAVY-body
heavy_script = """
def r = new java.util.Random().nextInt(100)
vars.put('branch', r < 50 ? '0' : '1')
"""
heavy_children = csv_dataset() + branch_preprocessor(heavy_script) + switch(
    sampler("POST /items (5 KB)", "/items", "POST", "heavyBody"),
    sampler("PUT /items/{id} (5 KB)", "/items/${item_id}", "PUT", "heavyBody"))

heavy_body = plan(
    "HEAVY-body (payload 5 KB)",
    "50% POST /items (5 KB) - 50% PUT /items/{id} (5 KB)",
    thread_group("HEAVY-body 30 threads", 30, heavy_children)
    + thread_group("HEAVY-body 60 threads", 60, heavy_children))

PLANS = {
    "read-heavy.jmx": read_heavy,
    "join-filter.jmx": join_filter,
    "mixed.jmx": mixed,
    "heavy-body.jmx": heavy_body,
}

if __name__ == "__main__":
    for filename, content in PLANS.items():
        with open(os.path.join(OUT, filename), "w", encoding="UTF-8") as fh:
            fh.write(content)
        print("écrit", os.path.join("jmeter", filename), len(content), "octets")
