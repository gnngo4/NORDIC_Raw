function NORDIC_main(mag, phase, base_out, x_kernel_dim, y_kernel_dim, z_kernel_dim, n_threads)
maxNumCompThreads(str2double(n_threads));
ARG.kernel_size_PCA = [str2double(x_kernel_dim) str2double(y_kernel_dim) str2double(z_kernel_dim)];
try
    NIFTI_NORDIC(mag, phase, base_out, ARG);
catch
end
end