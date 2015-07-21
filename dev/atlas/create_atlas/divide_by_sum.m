% Script to divide all generated tract by the sum of all tracts in order to 
% set the total sum to 1 for each pixel.


% create variable of tract numbering with 2 digits starting at 00
prefix_out = 'WM_and_GM_tract_';
ext = '.nii.gz';
label_left = [14 26 38 47 52 62 70 82 89 94 101 107 112 116 121];
label_right = [146 152 159 167 173 180 187 194 199 204 208 214 219 224 230];
% label_pve = [45 80 120 150 190 220 255];
label_GM = [45 80 120 150 190 220];
label_GM_left = [45 80 120];
label_GM_right = [150 190 220];
label_pve = [255];
label_values = [label_left, label_right, label_GM_left, label_GM_right, label_pve];


cell_tract = m_numbering(length(label_values), 2, 0);

cmd_sum = ['fslmaths ', prefix_out, '_', cell_tract{1}, ext];
cmd_sum_div = ['fslmaths ', prefix_out, '_', cell_tract{1}, '_div', ext];
cmd_display = ['fslview'];


% loop across tracts
for label = 1:length(label_values)
    % Extend command for sum (also takes CSF tract)
    if label~=1
        cmd_sum = [cmd_sum, ' -add ', prefix_out, '_', cell_tract{label}, ext];
        cmd_sum_div = [cmd_sum_div, ' -add ', prefix_out, '_', cell_tract{label}, '_div', ext];
    end
    
end

% sum of all tracts
cmd_sum = [cmd_sum, ' ', prefix_out, '_sum_all', ext];
disp(cmd_sum); [status,result] = unix(cmd_sum); if(status), error(result); end

% loop across tracts
for label = 1:length(label_values)
    % divide each slice by the sum of all tracts (even CSF)
    cmd = ['fslmaths ', prefix_out, '_', cell_tract{label}, ext, ' -div ', prefix_out, '_sum_all', ext, ' ', prefix_out, '_', cell_tract{label}, '_div', ext];
    disp(cmd); [status,result] = unix(cmd); if(status), error(result); end
    % Extend command display
    cmd_display = [cmd_display, ' ', prefix_out, '_', cell_tract{label}, '_div', ext];
end

% sum of all divided tracts
cmd_sum_div = [cmd_sum_div, ' ', prefix_out, '_sum_all_div', ext];
disp(cmd_sum_div); [status,result] = unix(cmd_sum_div); if(status), error(result); end

cmd_display = [cmd_display, '&'];
disp(cmd_display);
