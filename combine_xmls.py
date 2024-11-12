import os, sys
from xml.etree import ElementTree as et

home = os.getcwd()

xmls = [f for f in os.listdir(os.path.join(home, '..')) if f.endswith('.xml')]
xmls.sort()

def sort_element(root, element_name):
    unsorted_elements = []
    for element in root.findall(element_name):
        for subelement in element:
            atom_type_data = []
            for attribute_name in subelement.attrib.keys():
                atom_type_data.append(subelement.attrib.get(attribute_name))
            unsorted_elements.append(atom_type_data)
    sorted_elements = sorted(unsorted_elements, key=lambda x: x[0])

    for element in root.findall(element_name):
        for subelement, element_info in zip(element, sorted_elements):
            for attribute_name, attribute_value in zip(subelement.attrib.keys(), element_info):
                subelement.attrib[attribute_name] = attribute_value

# Sort elements within each xml and write sorted copy to current directory
for xml in xmls:
    xml_path = os.path.join(home , '..', xml)
    root = et.parse(xml_path)
    sort_element(root, 'AtomTypes')
    sort_element(root, 'HarmonicBondForce')
    sort_element(root, 'HarmonicAngleForce')
    sort_element(root, 'PeriodicTorsionForce')
    sort_element(root, 'NonbondedForce')

    resname = xml.split('.')[0]
    new_xml_path = os.path.join(home, xml)
    root.write(new_xml_path)

    os.system('sed -i "s/UNK/%s/g" %s' % (resname, new_xml_path))
    for element in root.findall('AtomTypes'):
        for subelement in element:
            type_name = subelement.attrib.get('name')
            new_type_name = type_name.replace('opls', resname)
            os.system('sed -i "s/%s/%s/g" %s' % (type_name, new_type_name, new_xml_path))
            class_name = subelement.attrib.get('class')
            if resname not in class_name:
                os.system('sed -i "s/%s/%s_%s/g" %s' % (class_name, class_name, resname, new_xml_path))


# Merge sorted xmls into single xml in current directory
xmls = [f for f in os.listdir() if f.endswith('.xml')]
xmls.sort()

# initialize
headers = []
top_xml_path = os.path.join(home, xmls[0])
top_tree = et.parse(top_xml_path)
for element in top_tree.findall('*'):
    headers.append(element)

for xml in xmls[1:]:
    xml_path = os.path.join(home, xml)
    tree = et.parse(xml_path)
    for element in tree.findall('*'):
        for header in headers:
            if header.tag == element.tag:
                for subelement in element:
                    new_subelement = et.SubElement(header, subelement.tag)
                    for sub_attribute in subelement.keys():
                        new_subelement.attrib[sub_attribute] = subelement.attrib[sub_attribute]
                    for subsubelement in subelement:
                        new_subsubelement = et.SubElement(new_subelement, subsubelement.tag)
                        for subsub_attribute in subsubelement.keys():
                            new_subsubelement.attrib[subsub_attribute] = subsubelement.attrib[subsub_attribute]
et.indent(top_tree, '  ')
merged_name = '_'.join([f.split('.')[0] for f in xmls]) + '.xml'
top_tree.write(merged_name, encoding="utf-8", xml_declaration=True)

# Delete sorted xmls
for xml in xmls:
    os.remove(xml)

# Add OPLS CustomNonbondedForce to merged xml
tree = et.parse(merged_name)
for nonbondedforce in tree.findall('NonbondedForce'):
    atom_types = []
    for nbf_atom_type in nonbondedforce:
        atom_types.append(nbf_atom_type.attrib.copy())
        nbf_atom_type.attrib['sigma'] = '1.0'
        nbf_atom_type.attrib['epsilon'] = '0.0'
    root = tree.getroot()
    customnonbondedforce = et.Element('CustomNonbondedForce')
    customnonbondedforce.attrib['energy'] = '4*E*((S/r)^12-(S/r)^6); E=sqrt(eps1*eps2); S=sqrt(sig1*sig2)'
    customnonbondedforce.attrib['bondCutoff'] = '3'
    customnonbondedforce.attrib['coulomb14scale'] = '0.0'
    customnonbondedforce.attrib['lj14scale'] = '0.5'
    ppp1 = et.SubElement(customnonbondedforce, 'PerParticleParameter')
    ppp1.attrib['name'] = 'sig'
    ppp2 = et.SubElement(customnonbondedforce, 'PerParticleParameter')
    ppp2.attrib['name'] = 'eps'
    for nbf_atom_type in atom_types:
        del nbf_atom_type['charge']
        nbf_atom_type['sig'] = nbf_atom_type.pop('sigma')
        nbf_atom_type['eps'] = nbf_atom_type.pop('epsilon')
        cnbf_atom_type = et.SubElement(customnonbondedforce, 'Atom')
        for attribute in nbf_atom_type.keys():
            cnbf_atom_type.attrib[attribute] = nbf_atom_type[attribute]
    root.append(customnonbondedforce)

et.indent(tree, '  ')
tree.write(merged_name, encoding="utf-8", xml_declaration=True)

