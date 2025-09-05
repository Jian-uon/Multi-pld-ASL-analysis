## Requirements

OS: linux/mac or windows(WSL) 

Softwares: FSL, anaconda/python

#### FSL installation link:

https://fsl.fmrib.ox.ac.uk/fsl/docs/#/install/windows

## Usage:

Open terminal and run:

1. "echo $FSLDIR"    (to ensure FSL installed)
2. "pip install oxasl"
3. "python -m pip install dcm2niix"


#### To process all subjects

python process_asl_data.py /path/to/input/directory /path/to/output/directory

#### To process a specific subject

python process_asl_data.py /path/to/input/directory /path/to/output/directory --subject subject_name


## Dataset structure

```
D:.
├─subject-1
│  ├─asl_3d_tra_10PLDs_Ctrl_1002
│  ├─asl_3d_tra_10PLDs_M0_1001
│  ├─asl_3d_tra_10PLDs_Tag_1003
│  └─t1_mx3d_sag_fs_0.6_a5_NIF_301
├─subject-2
│   ├─asl_3d_tra_10PLDs_Ctrl_1102
│   ├─asl_3d_tra_10PLDs_M0_1101
│   ├─asl_3d_tra_10PLDs_Tag_1103
│   └─t1_mx3d_sag_fs_0.6_a5_NIF_301
├─subject-3
...
```
