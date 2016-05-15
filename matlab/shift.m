%% Perliminaries

clear all; close all; clc; 

%Get files
files = dir('xyData*');
n = size(files,1);


%% Read files

for i = 1:n
    %Read tab file
    structure = tdfread(files(i).name);
    
    %Get model name
    name = files(i).name;
    underscores = strfind(name, '_');
    dot = strfind(name, '.');
    data(i).name = name(underscores(2)+1:dot-1);

    %Get variables
    field = fieldnames(structure);
  
    underscore = strfind(field(1),'_');
    name1 = char(field(1));
    data(i).x = eval(['structure.' name1]);
    
    underscore = strfind(field(2),'_');
    name2 = char(field(2));
    data(i).y = eval(['structure.' name2]);
    
    %Shift curves to start at 0,0
    %This removes all the first 0,0 exept one
    nonZero = find(data(i).y);
    firstNonZero = nonZero(1);
    data(i).y = data(i).y(firstNonZero-1:end);
    data(i).x = data(i).x(1:end-(firstNonZero-2));
    
    %% Wrtie to file
    f=fopen([data(i).name '.txt'],'w');
    fprintf(f, 'Time [s]\tPressure [MPa]\n');
    for j=1:length(data(i).x)
        fprintf(f,'%6d \t %6d\n',data(i).x(j), data(i).y(j));
    end
    fclose(f);
    
end


