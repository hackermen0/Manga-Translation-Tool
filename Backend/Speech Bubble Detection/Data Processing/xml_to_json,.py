import xml.etree.ElementTree as ET
import json

def xml_to_clean_dict(elem):
    d = {}
    
    # Include attributes directly
    d.update(elem.attrib)
    
    # Handle children
    children = list(elem)
    if children:
        for child in children:
            child_dict = xml_to_clean_dict(child)
            tag = child.tag

            if tag in d:
                # Already exists → make it a list
                if not isinstance(d[tag], list):
                    d[tag] = [d[tag]]
                d[tag].append(child_dict)
            else:
                d[tag] = child_dict
    else:
        # Leaf node: set text content if present
        if elem.text and elem.text.strip():
            d = elem.text.strip() if not elem.attrib else {**d, "text": elem.text.strip()}
    
    return d

tree = ET.parse('./Mangas/Nekodama/Nekodama.xml')
root = tree.getroot()
json_data = {root.tag: xml_to_clean_dict(root)}

with open("./Mangas/Nekodama/Nekodama.json", "w", encoding="utf-8") as f:

    print(json.dump(json_data, f, indent=2, ensure_ascii=False))