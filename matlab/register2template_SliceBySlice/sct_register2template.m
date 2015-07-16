function sct_register2template(file_reg,file_src,levels,file_ref,verbose)
% sct_register2template(file_reg,file_src,levels [,file_ref,verbose])
%-------------------------- FILES TO REGISTER -----------------------------------
% file_reg = {'data_highQ_mean_masked'}; % file to register
%--------------------------------------------------------------------------
% file_src = 'data_highQ_mean_masked';
%--------------------------------------------------------------------------
% %-----------------------------REFERENCE (DESTINATION)------------------------------------
% ref_fname = '/Volumes/users_hd2/tanguy/data/Boston/2014-07/Connectome/template/PD_template.nii.gz';%'/home/django/tanguy/matlab/spinalcordtoolbox/data/template/MNI-Poly-AMU_WM.nii.gz';
% levels_fname='/home/django/tanguy/matlab/spinalcordtoolbox/data/template/MNI-Poly-AMU_level.nii.gz';
% %--------------------------------------------------------------------------
dbstop if error

if ~exist('verbose','var')
    verbose=false;
end
log='log_applytransfo';
% levels=5:-1:2;
warp_transfo = 1;
[~,sct_dir] = unix('echo $SCT_DIR'); sct_dir(end)=[];

%-------------------------- FILES TO REGISTER -----------------------------------
% file_reg = {'data_highQ_mean_masked'}; % file to register
%--------------------------------------------------------------------------

%-----------------------------REFERENCE (DESTINATION)------------------------------------
if ~exist('file_ref','var'), file_ref=[sct_dir '/data/template/MNI-Poly-AMU_T2.nii.gz']; end;
levels_fname=[sct_dir '/data/template/MNI-Poly-AMU_level.nii.gz'];
%--------------------------------------------------------------------------


%--------------------------SOURCE FILE--------------------------------------
% data = 'KS_HCP35_crop_eddy_moco_lpca';
% scheme = 'KS_HCP.scheme';
% % Generate good source image (White Matter image)
% if ~exist([data '_ordered.nii'])
%     opt.fname_log = log;
%     sct_dmri_OrderByBvals(data,scheme,opt)
% end
% scd_generateWM([data '_ordered'],scheme,log);
% param.maskname='mask_spinal_cord';
% if ~exist(param.maskname)
%     param.file = 'data_highQ_mean';
%     scd_GenerateMask(param);
% end
% if ~exist('data_highQ_mean_masked.nii'), unix(['fslmaths data_highQ_mean -mul ' param.maskname ' data_highQ_mean_masked']), end
% file_src = 'data_highQ_mean_masked';
%----------------------------OR--------------------------------------------
% file_src = 'data_highQ_mean_masked';
%--------------------------------------------------------------------------


%--------------------------------------------------------------------------
%---------------------------DON'T CHANGE BELOW-----------------------------
%--------------------------------------------------------------------------
%--------------------------------------------------------------------------


% read template files
% read levels
levels_template=load_nii(levels_fname);
z_lev=[];
for i=levels
    [~,~,z]=find3d(levels_template.img==i); z_lev(end+1)=floor(mean(z));
end

% choose only good slices of the template
template=load_nii(file_ref);
template_roi=template.img(:,:,z_lev);
src_nii=load_nii(file_src); % use slice thickness of the source
template_roi=make_nii(double(template_roi),[template.hdr.dime.pixdim(2:3) src_nii.hdr.dime.pixdim(4)],[],[]);
save_nii(template_roi,'template_roi.nii')
file_ref = 'template_roi';


%--------------------------------------------------------------------------
% Estimate transfo between source and GW template
%--------------------------------------------------------------------------

sct_register_SbS(file_src,file_ref);



%--------------------------------------------------------------------------
% apply transfo
%--------------------------------------------------------------------------

for i_file_reg = 1:length(file_reg)
    
    % merge files
    %reg
    mergelist='';
    for iZ=1:freg.dims(3)
        mergelist=[mergelist sct_tool_remove_extension(files_reg{iZ},0) '_reg '];
    end
    cmd = ['fslmerge -z ' sct_tool_remove_extension(file_reg{i_file_reg},1) '_reg ' mergelist];
    j_disp(log,['>> ',cmd]); [status result] = unix(cmd); if status, error(result); end
    unix(['rm ' sct_tool_remove_extension(file_reg{i_file_reg},0) '_z*_reg*']);
    
    
end

% remove matrix
unix('rm -rf mat_level*');
% remove template
for level = 1:freg.dims(3), delete([files_ref{level} '*']); end
%delete([ref_fname '*']);
% display
if verbose
    unix(['fslview template_roi ' sct_tool_remove_extension(file_reg{1},1) '_reg /Volumes/taduv/data/Boston/2014-07/Connectome/template_roi/atlas/WMtract__16_roi.nii &']);
end