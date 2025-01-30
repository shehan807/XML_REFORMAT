"""
Module Name: LPG_reformatter.py
Authors: Shehan M. Parmar, John Hymel
Date: 2024-09-25
Description:
    This script reformats LigParGen XML file outputs by
        (1) renaming residues to useful, interpretable 3 character names,
        (2) sorts specific force elements, and
        (3) merges multiple residuce xmls into a single xml for OpenMM.
Usage:
    python LPG_reformatter.py --xml_files file1.xml file2.xml --output output.xml
"""

import os
import shutil
import argparse
from xml.etree import ElementTree as ET
from datetime import datetime

def parser():
    """
    Parses command-line arguments.

    Returns:
        args : Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Sort and merge ligpargen xml files for OpenMM input."
    )

    # Define required arguments
    parser.add_argument(
        "-x",
        "--xml_files",
        nargs="+",
        help="List of input XML files to be processed and merged.",
    )
    parser.add_argument("-o", "--output", help="Name of the output XML file.")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    args = parser.parse_args()
    if not args.xml_files:
        xmls = [f for f in os.listdir(os.getcwd()) if f.endswith(".xml")]
        args.xml_files = sorted(xmls)
    else:
        args.xml_files = sorted(args.xml_files)
    if not args.output:
        if os.path.exists("ffdir"):
            shutil.move("ffdir", f"ffdir_archive_{timestamp}")
        os.makedirs("ffdir")
        args.output = os.path.join(os.getcwd(), "ffdir")
    else:
        if os.path.exists(args.output):
            shutil.move(args.output, f"{args.output}_archive_{timestamp}")
        os.makedirs(args.output)
        args.output = os.path.join(os.getcwd(), args.output)

    return args


def create_sorted_xmls(xml_files, output_dir):
    sorted_xml_files = []
    for xml in xml_files:
        tree = ET.parse(xml)
        root = tree.getroot()

        for child in root:
            elements = []
            for element in root.findall(child.tag):
                for subelement in element:
                    atom_type_data = []
                    for attribute_name in subelement.attrib.keys():
                        atom_type_data.append(subelement.attrib.get(attribute_name))
                    elements.append(atom_type_data)
            sorted_elements = sorted(elements, key=lambda x: x[0])

            for element in root.findall(child.tag):
                for subelement, element_info in zip(element, sorted_elements):
                    for attribute_name, attribute_value in zip(
                        subelement.attrib.keys(), element_info
                    ):
                        subelement.attrib[attribute_name] = attribute_value

        resname = xml.split("/")[-1].split(".")[0]
        sorted_xml_file = os.path.join(output_dir, resname + "_sorted.xml")
        sorted_xml_files.append(sorted_xml_file)
        tree.write(sorted_xml_file)

        os.system('sed -i "s/UNK/%s/g" %s' % (resname, sorted_xml_file))
        for element in tree.findall("AtomTypes"):
            for subelement in element:
                type_name = subelement.attrib.get("name")
                new_type_name = type_name.replace("opls", resname)
                os.system(
                    'sed -i "s/%s/%s/g" %s'
                    % (type_name, new_type_name, sorted_xml_file)
                )
                class_name = subelement.attrib.get("class")
                if resname not in class_name:
                    os.system(
                        'sed -i "s/%s/%s_%s/g" %s'
                        % (class_name, class_name, resname, sorted_xml_file)
                    )
    return sorted_xml_files


def get_headers(xml_files):
    # Initialize an empty dictionary to collect all headers
    headers_dict = {}

    # First pass: Collect all unique headers from all XML files
    for xml in xml_files:
        tree = ET.parse(xml)
        for element in tree.getroot():
            if element.tag not in headers_dict:
                # Initialize a new header in the dictionary
                headers_dict[element.tag] = ET.Element(element.tag)
    return headers_dict


def merge_xmls(sorted_xml_files, output_dir):
    base_names = [
        os.path.splitext(os.path.basename(file.replace("_sorted", "")))[0]
        for file in sorted_xml_files
    ]
    output = os.path.join(output_dir, "_".join(base_names) + ".xml")

    # Parse the first XML file
    tree = ET.parse(sorted_xml_files[0])
    root = tree.getroot()

    # Iterate over the remaining XML files
    for xml_file in sorted_xml_files[1:]:
        data = ET.parse(xml_file).getroot()
        for elem in data:
            # Check if an element with the same tag already exists
            existing_elem = root.find(elem.tag)
            if existing_elem is not None:
                # If it exists, extend it with new elements
                existing_elem.extend(elem)
            else:
                # If it doesn't exist, append the new element
                root.append(elem)

    ET.indent(tree, "  ")
    tree.write(output, encoding="utf-8", xml_declaration=True)
    return output


def make_res_file(output):
    residue_file = output.split(".")[0] + "_residues.xml"

    tree = ET.parse(output)
    for residues in tree.findall("Residues"):
        new_tree = ET.ElementTree(residues)
        for residue in residues:
            atoms_dict = {}
            for index, atom in enumerate(residue):
                if atom.tag == "Atom":
                    atoms_dict[index] = atom.attrib["name"]
            for index, atom in enumerate(residue):
                if atom.tag == "Bond":
                    from_index = int(atom.attrib["from"])
                    from_name = atoms_dict[from_index]
                    atom.attrib["from"] = from_name

                    to_index = int(atom.attrib["to"])
                    to_name = atoms_dict[to_index]
                    atom.attrib["to"] = to_name

        ET.indent(new_tree, "  ")
        new_tree.write(residue_file, encoding="utf-8", xml_declaration=True)
    print(f"created {residue_file}")

def main():
    """
    Main function to process, sort, merge XML files and add custom non-bonded force.

    Returns:
        None
    """
    # Parse command-line arguments
    args = parser()
    sorted_xml_files = create_sorted_xmls(args.xml_files, args.output)
    print(sorted_xml_files)
    # ff_xml_file = merge_xmls(sorted_xml_files, args.output) # this causes a bug in the NonbondedForce 14scaled parameters
    for xml in sorted_xml_files:
        make_res_file(xml)
    #try: 
    #    make_res_file(sorted_xml_files)
    #except: 

    #    for xml in 


if __name__ == "__main__":
    main()
