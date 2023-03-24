from pathlib import Path

def init_nordic_derivatives_wf(
    output_dir: Path,
    outputs: Dict[str,Path],
    name: str
) -> None:

    from niworkflows.engine.workflows import LiterateWorkflow as Workflow
    from nipype.interfaces import utility as niu
    from nipype.pipeline import engine as pe
    from nipype.interfaces.io import ExportFile

    workflow = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields = [key for key in outputs.keys()]),
        name='inputnode'
    )

    ds_all = {}
    for key,path in outputs.items():
        ds_all[key] = pe.Node(
            ExportFile(
                out_file = path,
                check_extension = False,
                clobber=True
            ),
            name=f"ds_{key}",
            run_without_submitting=True,
        )
        workflow.connect([(inputnode, ds_all[key], [(key,'in_file')])])

    return workflow