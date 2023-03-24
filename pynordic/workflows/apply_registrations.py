from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

def init_apply_bold_to_anat_wf(
    slab_bold_quick=False,
    name="apply_bold_to_t1_wf"
):
    
    from niworkflows.engine.workflows import LiterateWorkflow as Workflow
    from pynordic.interfaces.bold_to_anat_transform import BoldToT1Transform
    from nipype.interfaces import fsl

    workflow = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "bold_file",
                "bold_ref",
                "bold_metadata",
                "fsl_hmc_affines",
                "bold_to_t1_warp",
                "t1_resampled"
            ]
        ),
        name="inputnode"
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["t1_space_bold",'t1_space_boldref']
        ),
        name="outputnode"
    )

    apply_bold_to_t1 = pe.Node(
        BoldToT1Transform(debug=slab_bold_quick),
        name="apply_bold_to_t1"
    )

    apply_bold_ref_to_t1 = pe.Node(
        fsl.ApplyWarp(),
        name='apply_bold_ref_to_t1'
    )

    workflow.connect([
        (inputnode,apply_bold_to_t1,[
            ("bold_file","bold_path"),
            (("bold_metadata",_get_metadata,"RepetitionTime"),"repetition_time"),
            ("fsl_hmc_affines","hmc_mats"),
            ("bold_to_t1_warp","bold_to_t1_warp"),
            ("t1_resampled","t1_resampled")
        ]),
        (apply_bold_to_t1,outputnode,[('t1_bold_path','t1_space_bold')]),
        (inputnode,apply_bold_ref_to_t1,[
            ('bold_ref','in_file'),
            ('t1_resampled','ref_file'),
            ('bold_to_t1_warp','field_file'),
        ]),
        (apply_bold_ref_to_t1,outputnode,[('out_file','t1_space_boldref')])
    ])

    return workflow

def _get_metadata(metadata_dict,_key):

    assert _key in metadata_dict, f"{_key} not found in metadata."

    return metadata_dict[_key]