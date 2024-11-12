import os, sys
from xml.etree import ElementTree as et

xml_file = 'H20_SAL_TBA.xml'
residue_file = xml_file.split('.')[0] + '_residues.xml'

tree = et.parse(xml_file)
for residues in tree.findall('Residues'):
    new_tree = et.ElementTree(residues)
    for residue in residues:
        atoms_dict = {}
        for index, atom in enumerate(residue):
            if atom.tag == 'Atom':
                atoms_dict[index] = atom.attrib['name']
        for index, atom in enumerate(residue):
            if atom.tag == 'Bond':
                from_index = int(atom.attrib['from'])
                from_name = atoms_dict[from_index]
                atom.attrib['from'] = from_name

                to_index = int(atom.attrib['to'])
                to_name = atoms_dict[to_index]
                atom.attrib['to'] = to_name

    et.indent(new_tree, '  ')
    new_tree.write(residue_file, encoding="utf-8", xml_declaration=True)


