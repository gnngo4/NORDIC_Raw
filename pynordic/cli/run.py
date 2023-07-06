import certifi, sys, os
os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(os.path.dirname(sys.argv[0]),certifi.where())

import typer
from typing import Optional

from pathlib import Path

from bids import BIDSLayout

from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from nipype.algorithms.misc import Gzip
from nipype.algorithms.confounds import TSNR
from niworkflows.interfaces.nibabel import GenerateSamplingReference
from fmriprep.workflows.bold.stc import init_bold_stc_wf

sys.path.append('/opt/pynordic')
from pynordic.workflows.derivatives.utils import PipelineManager
from pynordic.workflows.bold_reference import init_bold_ref_wf
from pynordic.workflows.apply_registrations import init_apply_bold_to_anat_wf
from pynordic.workflows.derivatives.outputs import init_nordic_derivatives_wf
from pynordic.interfaces.nordic import Nordic

def main(
    out_dir: Path,
    bids_dir: Path,
    preproc_dir: Path,
    sub_id: str,
    ses_id: str,
    task_id: str,    
    run_id: str,
    nordic_patch_size_estimator: str,
    n_threads: int,
    scratch_dir: Optional[Path] = '/tmp'
):

    # Set-up
    manager = PipelineManager(
        bids_dir,
        preproc_dir,
        out_dir,
        sub_id,
        ses_id,
        task_id,
        run_id
    )
    manager.create_output_directory_tree()
    inputs = manager.get_inputs()
    outputs, output_flag = manager.get_outputs()
    # Check if all inputs exist.
    if len(inputs) != 6:
        print(f"Some inputs are missing.\nExiting the program.")
        sys.exit()
    # Check if NORDIC denoising has already been ran.
    if output_flag:
        print(f"Outputs are already exist.\nExiting the program.")
        sys.exit()
    # Get metadata for the bold nifti
    layout = BIDSLayout(bids_dir)
    metadata = layout.get_metadata(inputs['bold_part-mag'])
    if not bool(metadata["SliceTiming"]):
        raise ValueError("SliceTiming metadata is unavailable.")

    """
    Workflow
    """
    workflow = Workflow(
        name = f'NORDIC_sub-{sub_id}_session-{ses_id}',
        base_dir = scratch_dir
    )

    inputnode = pe.Node(
        niu.IdentityInterface(
            [
                'anat_image',
                'mag_image',
                'phase_image',
                'reference_image',
                'out_image',
                'n_threads',
                'hmc_affines_tar',
                'bold_to_anat_warp',
            ]
        ),
        name='inputnode'
    )
    inputnode.inputs.anat_image = str(inputs['anat'])
    inputnode.inputs.mag_image = str(inputs['bold_part-mag'])
    inputnode.inputs.phase_image = str(inputs['bold_part-phase'])
    inputnode.inputs.reference_image = str(inputs['bold_reference'])
    inputnode.inputs.hmc_affines_tar = str(inputs['bold_hmc_affines'])
    inputnode.inputs.bold_to_anat_warp = str(inputs['bold_to_anat_warp'])
    inputnode.inputs.n_threads = n_threads

    nordic_patch_size_buffer = pe.Node(
        niu.IdentityInterface(
            ['patch_size']
        ),
        name='nordic_patch_size_buffer'
    )

    bold_ref = init_bold_ref_wf(
        str(inputs['bold_part-mag']),
        name='bold_reference_wf'
    )

    nordic_proc = pe.Node(
        Nordic(out_image='nordic_processed'),
        name='nordic_process'
    )

    nordic_gzip = pe.Node(
        Gzip(mode="compress"),
        name='nordic_gzip'
    )

    nordic_stc_wf = init_bold_stc_wf(
        metadata=metadata,
        name='stc_wf'
    )
    nordic_stc_wf.inputs.inputnode.skip_vols = 0

    nordic_bold_to_anat_wf = init_apply_bold_to_anat_wf(
        slab_bold_quick=False,
        name=f"nordic_trans_bold_to_anat_wf"
    )
    nordic_bold_to_anat_wf.inputs.inputnode.bold_metadata = metadata

    nordic_tsnr = pe.Node(
        TSNR(),
        name='nordic_tsnr'
    )

    raw_tsnr = pe.Node(
        TSNR(),
        name='raw_tsnr'
    )

    nordic_derivatives_wf = init_nordic_derivatives_wf(
        out_dir,
        outputs,
        name='nordic_derivatives_wf'
    )

    workflow.connect([
        (inputnode,bold_ref,[('mag_image','inputnode.bold')]),
        (inputnode,nordic_proc,[
            ('mag_image','mag_image'),
            ('phase_image','phase_image'),
            ('n_threads','n_threads'),
        ]),
        (inputnode,nordic_patch_size_buffer,[(('mag_image',_estimate_patch_size,nordic_patch_size_estimator),'patch_size')]),
        (nordic_patch_size_buffer,nordic_proc,[
            (('patch_size',_index_list,0),'patch_x_dim'),
            (('patch_size',_index_list,1),'patch_y_dim'),
            (('patch_size',_index_list,2),'patch_z_dim'),
        ]),
        (nordic_proc,nordic_gzip,[('out_image','in_file')]),
        (nordic_gzip,nordic_tsnr,[('out_file','in_file')]),
        (inputnode,raw_tsnr,[('mag_image','in_file')]),
        (nordic_gzip,nordic_stc_wf,[('out_file','inputnode.bold_file')]),
        (nordic_stc_wf, nordic_bold_to_anat_wf,[('outputnode.stc_file','inputnode.bold_file')]),
        (bold_ref,nordic_bold_to_anat_wf,[('outputnode.boldref','inputnode.bold_ref')]),
        (inputnode,nordic_bold_to_anat_wf,[
		('reference_image', 'inputnode.t1_resampled'),
		('bold_to_anat_warp', 'inputnode.bold_to_t1_warp'),
		(('hmc_affines_tar', _untar), 'inputnode.fsl_hmc_affines'),
	]),
        (raw_tsnr,nordic_derivatives_wf,[('tsnr_file','inputnode.tsnr_raw')]),
        (nordic_tsnr,nordic_derivatives_wf,[('tsnr_file','inputnode.tsnr_nordic')]),
        (nordic_bold_to_anat_wf,nordic_derivatives_wf,[('outputnode.t1_space_bold','inputnode.bold_nordic')]),
    ])

    workflow.run()

def _index_list(X,idx):
    return X[idx]

def _untar(tar,outdir='/tmp/hmc_mats'):
    from pathlib import Path
    import tarfile
    with tarfile.open(tar,'r:gz') as tar:
        tar.extractall(outdir)
    paths = list(Path(outdir).iterdir())
    paths.sort()
    
    return paths

def _estimate_patch_size(nifti,estimator='ISO',x_custom=None,y_custom=None,z_custom=None):
    
    ESTIMATOR_OPTIONS = ['ISO','SLAB','CUSTOM']
    if estimator not in ESTIMATOR_OPTIONS:
        raise ValueError(f"estimator must be one of {ESTIMATOR_OPTIONS}.")
    
    
    import nibabel as nib
    
    x,y,z,t = nib.load(nifti).get_fdata().shape
    
    # Voxel:Timepoint == 11:1
    if estimator == 'ISO':
        x_p = int( (11 * t) ** (1/3) )
        y_p, z_p = x_p, x_p
        
    if estimator == 'SLAB':
        z_p = z
        x_p = int( (11*t/z) ** (1/2) )
        y_p = x_p
        
    if estimator == 'CUSTOM':
        assert x_custom is not None \
            and y_custom is not None \
            and z_custom is not None, \
        f"Custom parameters are not set."
        return x_custom, y_custom, z_custom
        
    else:
        NotImplemented
    
    return x_p, y_p, z_p


if __name__ == '__main__':
    typer.run(main)
