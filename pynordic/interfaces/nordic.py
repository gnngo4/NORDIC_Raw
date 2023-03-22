import os, pathlib

from nipype.interfaces.base import (
    CommandLine,
    CommandLineInputSpec,
    File,
    TraitedSpec,
    traits,
)

class NordicInputSpec(CommandLineInputSpec):
    mag_image = File(
        exists=True,
        mandatory=True,
        argstr='%s',
        position=0,
        desc='magnitude image',
    )
    phase_image = File(
        exists=True,
        mandatory=True,
        argstr='%s',
        position=1,
        desc='phase image',
    )
    out_image = File(
        exists=False,
        mandatory=True,
        argstr='%s',
        position=2,
        desc='NORDIC denoised image',
    )
    patch_x_dim = traits.Int(
        mandatory=True,
        argstr='%s',
        position=3,
        desc='PCA patch size (x-dim)',
    )
    patch_y_dim = traits.Int(
        mandatory=True,
        argstr='%s',
        position=4,
        desc='PCA patch size (y-dim)',
    )
    patch_z_dim = traits.Int(
        mandatory=True,
        argstr='%s',
        position=5,
        desc='PCA patch size (z-dim)',
    )
    n_threads = traits.Int(
        mandatory=True,
        argstr='%s',
        position=6,
        desc='Number of threads',
    )

class NordicOutputSpec(TraitedSpec):
    out_image = File(
        desc='NORDIC denoised image'
    )

class Nordic(CommandLine):
    _cmd = '/opt/nordic_compiled/run_nordic_main.sh /opt/matlab'
    input_spec, output_spec = NordicInputSpec, NordicOutputSpec

    def _list_outputs(self):
        _outputs = {
            'out_image': pathlib.Path(f"{self.inputs.out_image}.nii").resolve(),
        }

        return _outputs