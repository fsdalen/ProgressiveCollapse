%% Plot curves

%{
This takes multiple files and plots the data

FileName: xyData_header_curveName.txt
    curveName: Name of curve
    header: what is plotted, currently ignored


File should be tabular delimided with with two columns
First row is ignored as headers.
Legend is created from curveName
X and Y labels are manual at the end of the script
%}

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
end



%% Plot

colors = distinguishable_colors(n);
legendPlot = [];

figure(1)
ax = gca;
ax.FontSize = 12;       %Changes font size of the axes (default = 10). Legend font size is by default 90% of axes
set(gca,'DefaultLineLineWidth',1)  %Change line width. Default = 0.5

hold on
for i = 1:n
    h = plot(data(i).x, data(i).y ,'color' ,colors(i,:));
    eval(['h' num2str(i) ' = h;'])                           %Number the handle, e.g. h1
    eval(['legendPlot(' num2str(i) ') = h' num2str(i) ';']) %Put the handle into the legendPlot vector, which we will later relate lengendText
end
grid on
legend(legendPlot,data.name)
xlabel('Time [s]')
ylabel('Displacement [mm]')
