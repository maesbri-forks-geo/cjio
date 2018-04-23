
import os
import sys
import json
import collections
import jsonref
import urllib
from pkg_resources import resource_filename

import validation

class CityJSON:

    def __init__(self, file, ignore_duplicate_keys=False):
        if ignore_duplicate_keys == True:
            self.j = json.loads(file.read())
        else:
            try:
                self.j = json.loads(file.read(), object_pairs_hook=validation.dict_raise_on_duplicates)
            except ValueError as err:
                raise ValueError(err)
        #-- a CityJSON file?
        if "type" in self.j and self.j["type"] == "CityJSON":
            pass
        else:
            self.j = {}
            raise ValueError("Not a CityJSON file")

    def fetch_schema(self):
        #-- fetch proper schema
        if self.j["version"] == "0.6":
            schema = resource_filename(__name__, '/schemas/v06/cityjson.json')
        elif self.j["version"] == "0.5":
            schema = resource_filename(__name__, '/schemas/cityjson-v05.schema.json')
        else:
            return (False, None)
        #-- open the schema
        fins = open(schema)
        jtmp = json.loads(fins.read())
        fins.seek(0)
        if "$id" in jtmp:
            u = urllib.urlparse(jtmp['$id'])
            os.path.dirname(u.path)
            base_uri = u.scheme + "://" + u.netloc + os.path.dirname(u.path) + "/" 
        else:
            abs_path = os.path.abspath(os.path.dirname(schema))
            base_uri = 'file://{}/'.format(abs_path)
        js = jsonref.loads(fins.read(), jsonschema=True, base_uri=base_uri)
        return (True, js)

    def fetch_schema_cityobjects(self):
        #-- fetch proper schema
        if self.j["version"] == "0.6":
            schema = resource_filename(__name__, '/schemas/v06/cityjson.json')
        elif self.j["version"] == "0.5":
            schema = resource_filename(__name__, '/schemas/cityjson-v05.schema.json')
        else:
            return (False, None)
        sco_path = os.path.abspath(os.path.dirname(schema))
        sco_path += '/cityobjects.json'
        jsco = json.loads(open(sco_path).read())
        return (True, jsco)

    def validate(self, skip_schema=False):
        es = ""
        ws = ""
        #-- 1. schema
        if skip_schema == False:
            b, js = self.fetch_schema()
            if b == False:
                return (False, "Can't find the proper schema.", "")
            else:
                try:
                    validation.validate_against_schema(self.j, js)
                except Exception as e:
                    es += str(e)
                    return (False, es, "")
        #-- 2. ERRORS
        isValid = True
        b, errs = validation.city_object_groups(self.j) 
        if b == False:
            isValid = False
            es += errs
        b, errs = validation.building_parts(self.j) 
        if b == False:
            isValid = False
            es += errs
        b, errs = validation.building_installations(self.j)
        if b == False:
            isValid = False
            es += errs
        b, errs = validation.building_pi_parent(self.j)
        if b == False:
            isValid = False
            es += errs
        b, errs = validation.semantics(self.j)
        if b == False:
            isValid = False
            es += errs
        #-- 3. WARNINGS
        woWarnings = True
        b, errs = validation.metadata(self.j, js) 
        if b == False:
            woWarnings = False
            ws += errs
        b, errs = validation.cityjson_properties(self.j, js)
        if b == False:
            woWarnings = False
            ws += errs
        b, errs = validation.geometry_empty(self.j)
        if b == False:
            woWarnings = False
            ws += errs
        b, errs = validation.duplicate_vertices(self.j)
        if b == False:
            woWarnings = False
            ws += errs
        b, errs = validation.orphan_vertices(self.j)
        if b == False:
            woWarnings = False
            ws += errs
        #-- fetch schema cityobjects.json
        b, jsco = self.fetch_schema_cityobjects()
        b, errs = validation.citygml_attributes(self.j, jsco)
        if b == False:
            woWarnings = False
            ws += errs
        return (isValid, woWarnings, es, ws)

    def update_bbox(self):
        """
        Update the bbox (["metadata"]["bbox"]) of the CityJSON.
        If there is none then it is added.
        """
        bbox = [9e9, 9e9, 9e9, -9e9, -9e9, -9e9]
        for v in self.j["vertices"]:
            for i in range(3):
                if v[i] < bbox[i]:
                    bbox[i] = v[i]
            for i in range(3):
                if v[i] > bbox[i+3]:
                    bbox[i+3] = v[i]
        if "metadata" not in self.j:
            self.j["metadata"] = {}
        if "transform" in self.j:
            for i in range(3):
                bbox[i] = (bbox[i] * self.j["transform"]["scale"][i]) + self.j["transform"]["translate"][i]
            for i in range(3):
                bbox[i+3] = (bbox[i+3] * self.j["transform"]["scale"][i]) + self.j["transform"]["translate"][i]
        self.j["metadata"]["bbox"] = bbox
        return bbox        

    def update_crs(self, newcrs):
        if "metadata" not in self.j:
            self.j["metadata"] = {}
        if "crs" not in self.j["metadata"]:
            self.j["metadata"]["crs"] = {} 
        if "epsg" not in self.j["metadata"]["crs"]:
            self.j["metadata"]["crs"]["epsg"] = None
        try:
            i = int(newcrs)
            self.j["metadata"]["crs"]["epsg"] = i
            return True
        except ValueError:
            return False

    
    def subset(self, lsIDs, box):
        print (lsIDs)
        print (box)

    def remove_textures(self):
        for i in self.j["CityObjects"]:
            if "texture" in self.j["CityObjects"][i]:
                del self.j["CityObjects"][i]["texture"]
        if "appearance" in self.j:
            if "textures" in self.j["appearance"]:
                del self.j["appearance"]["textures"]
            if "vertices-texture" in self.j["appearance"]:
                del self.j["appearance"]["vertices-texture"]
            if "default-theme-texture" in self.j["appearance"]:
                del self.j["appearance"]["default-theme-texture"]
        print (len(self.j["appearance"]))
        if self.j["appearance"] is None or len(self.j["appearance"]) == 0:
            del self.j["appearance"]
        return True


    def remove_materials(self):
        for i in self.j["CityObjects"]:
            if "material" in self.j["CityObjects"][i]:
                del self.j["CityObjects"][i]["material"]
        if "appearance" in self.j:
            if "materials" in self.j["appearance"]:
                del self.j["appearance"]["materials"]
            if "default-theme-material" in self.j["appearance"]:
                del self.j["appearance"]["default-theme-material"]
        if self.j["appearance"] is None or len(self.j["appearance"]) == 0:
            del self.j["appearance"]
        return True

    def get_info(self):
        info = collections.OrderedDict()
        info["cityjson_version"] = self.j["version"]
        if "crs" in self.j["metadata"] and "epsg" in self.j["metadata"]["crs"]:
            info["crs"] = self.j["metadata"]["crs"]["epsg"]
        else:
            info["crs"] = None
        if "bbox" in self.j["metadata"]:
            info["bbox"] = self.j["metadata"]["bbox"]
        else:
            info["bbox"] = None
        info["cityobjects_total"] = len(self.j["CityObjects"])
        info["vertices_total"] = len(self.j["vertices"])
        d = set()
        for key in self.j["CityObjects"]:
            d.add(self.j['CityObjects'][key]['type'])
        info["cityobjects_present"] = list(d)
        d.clear()
        for key in self.j["CityObjects"]:
            for geom in self.j['CityObjects'][key]['geometry']:
                d.add(geom["type"])
        info["geom_primitives_present"] = list(d)
        if 'appearance' in self.j:
            info["materials"] = 'materials' in self.j['appearance']
            info["textures"] = 'textures' in self.j['appearance']
        else:
            info["materials"] = False
            info["textures"] =  False
        return json.dumps(info, indent=2)




if __name__ == '__main__':
    with open('/Users/hugo/projects/cityjson/example-datasets/dummy-values/invalid.json', 'r') as cjfile:
    # with open('/Users/hugo/projects/cityjson/example-datasets/dummy-values/invalid3.json', 'r') as cjfile:
    # with open('example2.json', 'r') as cjfile:
    # with open('bob.json', 'r') as cjfile:
    # with open('/Users/hugo/Dropbox/data/cityjson/examples/rotterdam/3-20-DELFSHAVEN.json', 'r') as cjfile:
        try:
            d = CityJSON(cjfile, ignore_duplicate_keys=False)
        except ValueError:
            print ("!!!duplicate keys")
            sys.exit()

    b, errs = d.validate()            
    if b == False:
        print (errs)

    print ("done.")
