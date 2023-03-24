"""
derivatives/nordic_denoise/bold_preproc/sub-?/ses-?/func/
    - tsnr before
    - tsnr after
    - proc-NORDIC_bold.nii.gz
"""

import glob
from pathlib import Path

class PipelineManager:

    def __init__(
        self,
        bids_dir: Path,
        preproc_dir: Path,
        out_dir: Path,
        sub_id: str,
        ses_id: str,
        task_id: str,
        run_id: str
        ):

        self.bids_dir = bids_dir
        self.preproc_dir = preproc_dir
        self.out_dir = out_dir
        self.sub_id = sub_id
        self.ses_id = ses_id
        self.task_id = task_id
        self.run_id = run_id
        self.directory_path = Path(f"{self.out_dir}/sub-{self.sub_id}/ses-{self.ses_id}/func")

    def create_output_directory_tree(self) -> None:

        self.directory_path.mkdir(parents=True,exist_ok=True)

    def get_inputs(self):

        all_inputs_exist = True
        
        inputs = {}
        # processed t1w
        inputs['anat'] = _find_file(self.preproc_dir,f"*sub-{self.sub_id}*desc-preproc_T1w.nii.gz")
        # raw bold
        inputs['bold_part-mag'] = _find_file(self.bids_dir,f'*sub-{sub_id}_ses-{ses_id}_task-{task_id}*run-{run_id}_part-mag_bold.nii.gz')
        inputs['bold_part-phase'] = _find_file(self.bids_dir,f'*sub-{sub_id}_ses-{ses_id}_task-{task_id}*run-{run_id}_part-phase_bold.nii.gz')
        # processed reg files
        inputs['bold_hmc_affines'] = _find_file(self.preproc_dir,f'*sub-{sub_id}_ses-{ses_id}_task-{task_id}*run-{run_id}_hmc.mats.tar.gz')
        inputs['bold_to_anat_warp'] = _find_file(self.preproc_dir,f'*sub-{sub_id}_ses-{ses_id}_task-{task_id}*run-{run_id}_from-slab_to-T1w_warp.nii.gz')

        for k,v in inputs.items():
            if not Path(v).exists():
                all_inputs_exist = False
        
        if all_inputs_exist:
            return inputs
        else:
            return {}

    def get_outputs(self):

        all_outputs_exist = True

        outputs = {'run_flag': True}
        # outputs
        base = _find_file(self.bids_dir,f'*sub-{sub_id}_ses-{ses_id}_task-{task_id}*run-{run_id}_part-mag_bold.nii.gz')
        outputs['tsnr_raw'] = Path(f"{self.directory_path}/{str(base.split('/')[-1]).replace('_part-mag_bold.nii.gz','_desc-raw_tSNR.nii.gz')}")
        outputs['tsnr_nordic'] = Path(f"{self.directory_path}/{str(base.split('/')[-1]).replace('_part-mag_bold.nii.gz','_desc-nordic_tSNR.nii.gz')}")
        outputs['bold_nordic'] = Path(f"{self.directory_path}/{str(base.split('/')[-1]).replace('_part-mag_bold.nii.gz','_proc-nordic_bold.nii.gz')}")

        for k,v in outputs.items():
            if not Path(v).exists():
                outputs['run_flag'] = False

        return outputs

    def _find_file(root_path, file_pattern):
    
        file_paths  = list(Path(root_path).rglob(file_pattern))
        if len(file_paths) != 1:
            raise ValueError(f"Error: {len(file_paths)} paths were found. 1 path is expected.")
        
        for file_path in file_paths:
            return file_path