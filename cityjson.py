
import sys
import json
import collections

import validation

class CityJSON:

    def __init__(self, file):
        try:
            self.j = json.loads(file.read(), object_pairs_hook=validation.dict_raise_on_duplicates)
        except ValueError, Argument:
            raise ValueError(Argument)
        #-- a CityJSON file?
        if "type" in self.j and self.j["type"] == "CityJSON":
            pass
        else:
            self.j = {}
            raise ValueError("Not a CityJSON file")

    def validate(self):
        try:
            validation.validate_cityjson(self.j)
        except Exception as e:
            return (False, e)
        return (True, "")

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
        info["materials"] = 'materials' in self.j['appearance']
        info["textures"] = 'textures' in self.j['appearance']
        return json.dumps(info, indent=2)




if __name__ == '__main__':
    with open('/Users/hugo/projects/cityjson/example-datasets/dummy-values/invalid.json', 'r') as cjfile:
    # with open('example2.json', 'r') as cjfile:
    # with open('bob.json', 'r') as cjfile:
        try:
            d = CityJSON(cjfile)
        except ValueError:
            print "oups"
            sys.exit()

    d.validate()            
    # print d.update_crs(888)
    # print d.update_crs("hguo")
    # print d.j["metadata"]

    # print e.j