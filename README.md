# XML_REFORMAT
Sort, Merge, and Reformat any number of OpenMM XML files produced by LigParGen

## Instructions

After cloning the repository, the code can be used to create an output directory (default to `ffdir`) containing a combined XML file of any number of LigParGen generated XML files. An example is shown in the `tests` directory, where the combined .XML file is created via:

```python
python LPG_reformat.py --xml_files tests/TBA_SAL_H2O/SAL.xml tests/TBA_SAL_H2O/H2O.xml tests/TBA_SAL_H2O/TBA.xml --output tests/TBA_SAL_H2O/ffdir
```
