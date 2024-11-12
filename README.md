# XML_REFORMAT
Sort, Merge, and Reformat any number of OpenMM XML files produced by LigParGen

## Instructions

After cloning the repository, the code can be used to create an output directory (default to `ffdir`) containing a combined XML file of any number of LigParGen generated XML files. An example is shown in the `tests` directory, where the combined .XML file is created via:

```bash
python LPG_reformat.py
    --xml_files tests/TBA_SAL_H2O/SAL.xml tests/TBA_SAL_H2O/H2O.xml tests/TBA_SAL_H2O/TBA.xml
    --output tests/TBA_SAL_H2O/ffdir
```

### NOTE (!):

The CustomNonbondedForce in OpenMM implements the Lorentz-Berthelot combination rules to estimate sigma and epsilon parameters for 1-2, 1-3, and 1-4 interactions. However, correctly implementing the OPLS-AA geometric combination rules requires modification of the OpenMM system, which is best done during simulation calls. i.e., **the final merged .xml file is incorrect without the following function call:**

```python
def OPLS_LJ(system):
    forces = {system.getForce(index).__class__.__name__: system.getForce(
        index) for index in range(system.getNumForces())}
    nonbonded_force = forces['NonbondedForce']
    lorentz = CustomNonbondedForce(
        '4*epsilon*((sigma/r)^12-(sigma/r)^6); sigma=sqrt(sigma1*sigma2); epsilon=sqrt(epsilon1*epsilon2)')
    lorentz.setNonbondedMethod(nonbonded_force.getNonbondedMethod())
    lorentz.addPerParticleParameter('sigma')
    lorentz.addPerParticleParameter('epsilon')
    lorentz.setCutoffDistance(nonbonded_force.getCutoffDistance())
    system.addForce(lorentz)
    LJset = {}
    for index in range(nonbonded_force.getNumParticles()):
        charge, sigma, epsilon = nonbonded_force.getParticleParameters(index)
        LJset[index] = (sigma, epsilon)
        lorentz.addParticle([sigma, epsilon])
        nonbonded_force.setParticleParameters(
            index, charge, sigma, epsilon * 0)
    for i in range(nonbonded_force.getNumExceptions()):
        (p1, p2, q, sig, eps) = nonbonded_force.getExceptionParameters(i)
        # ALL THE 12,13 and 14 interactions are EXCLUDED FROM CUSTOM NONBONDED
        # FORCE
        lorentz.addExclusion(p1, p2)
        if eps._value != 0.0:
            #print p1,p2,sig,eps
            sig14 = sqrt(LJset[p1][0] * LJset[p2][0])
            eps14 = sqrt(LJset[p1][1] * LJset[p2][1])
            nonbonded_force.setExceptionParameters(i, p1, p2, q, sig14, eps)
    return system
``` 
