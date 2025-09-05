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